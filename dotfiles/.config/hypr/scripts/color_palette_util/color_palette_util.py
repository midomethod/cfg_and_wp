#!/usr/bin/env python3

import argparse
from PIL import Image
import numpy as np
import colorsys

def get_hsv(color_tuple_or_obj):
    if isinstance(color_tuple_or_obj, tuple):
        return colorsys.rgb_to_hsv(*color_tuple_or_obj[:3])
    return colorsys.rgb_to_hsv(*color_tuple_or_obj.color[:3])

class ColorTracker:
    def __init__(self, color=None, weight=1):
        self.weight = weight if color else 0
        self.color = tuple(int(e) for e in color) if color else None

    def avg_add(self, color, multiplicity=1):
        # Populate new color if 
        if not self.color:
            self.color = (int(e) for e in color) 
            self.weight = multiplicity
            return

        # Update color with weighted average
        self.color = (
            (self.color[0]*self.weight + int(color[0])*multiplicity) // (self.weight + multiplicity),
            (self.color[1]*self.weight + int(color[1])*multiplicity) // (self.weight + multiplicity),
            (self.color[2]*self.weight + int(color[2])*multiplicity) // (self.weight + multiplicity),
        )

        # Update weight
        self.weight = self.weight + multiplicity

    def rpr_add(self, color, multiplicity=1):
        self.weight = self.weight + multiplicity
        self_sat = get_hsv(self.color)[1]
        new_sat = get_hsv(color)[1]

        # Update color if more saturated
        if self_sat <= new_sat:
            self.color = color

    def __repr__(self):
        return f"ColorTracker(color={self.color}, weight={self.weight})"

def unify_palette(color_tracker_list):
    avg_sat = (
            sum([float(get_hsv(ct)[1]) * ct.weight for ct in color_tracker_list]) 
            / sum([ct.weight for ct in color_tracker_list])
        )
    avg_val = int(
            sum([float(get_hsv(ct)[2]) * ct.weight for ct in color_tracker_list]) 
            / sum([ct.weight for ct in color_tracker_list])
    )
    return [
            ColorTracker(
                color=colorsys.hsv_to_rgb(
                        get_hsv(ct)[0],
                        avg_sat,
                        avg_val
                    ),
                weight=ct.weight,
            )
            for ct in color_tracker_list
        ]

def naive_color_distance(pixel_1, pixel_2):
    p1_tup = tuple(pixel_1)
    p2_tup = tuple(pixel_2)

    # Theoretical max distance is 256*3=768 between 0x000000 and 0xFFFFFF
    r_dist = abs(int(p1_tup[0])-int(p2_tup[0]))
    g_dist = abs(int(p1_tup[1])-int(p2_tup[1]))
    b_dist = abs(int(p1_tup[2])-int(p2_tup[2]))
    return r_dist + g_dist + b_dist

def rectilinear_redmean_distance(pixel_1, pixel_2):
    p1_tup = tuple(pixel_1)
    p2_tup = tuple(pixel_2)

    r1, g1, b1, *rest1 = p1_tup
    r2, g2, b2, *rest2 = p2_tup

    r_bar = ( int(r1) + int(r2) ) // 2

    wR = 0.5 + r_bar / 512
    wB = 0.5 + (256 - r_bar) / 512
    wG = 1.0

    r_dist = abs(int(p1_tup[0])-int(p2_tup[0]))
    g_dist = abs(int(p1_tup[1])-int(p2_tup[1]))
    b_dist = abs(int(p1_tup[2])-int(p2_tup[2]))
 
    return wR * r_dist + wG * g_dist + wB * b_dist

def show_color(color_triple):
    r, g, b, *rest = color_triple
    print(f'\x1b[48;2;{r};{g};{b}m    \x1b[0m', end='')  # 2 space blocks

def show_palette(color_tracker_list, hsv=False):
    for ct in color_tracker_list:
        triple = ct.color
        r, g, b, *rest = triple
        show_color(triple)
        print(f"\tHex: 0x{r:02x}{g:02x}{b:02x}, n={ct.weight}{' HSV: ' if hsv else ''}{get_hsv((r, g, b)) if hsv else ''}")
    print()

def infer_color_palette(
        image_path,
        sampling_rate,
        num_output,
        color_sep,
        distance_function_str,
        grouping_method_str,
    ):

    df = {
        'naive': naive_color_distance,
        'rrm': rectilinear_redmean_distance,
        }[distance_function_str]
    gm = {
        'avg': ColorTracker.avg_add,
        'rpr': ColorTracker.rpr_add,
        }[grouping_method_str]

    with Image.open(image_path) as img:
        print(f'Starting with {image_path}')
        pxl_arr = np.array(img)
       
        print(f'Image dimensions: ({pxl_arr.shape[0]}, {pxl_arr.shape[1]}, {pxl_arr.shape[2]})')
        pixel_traversed = 0
        color_dict = dict()

        for y in range(0, pxl_arr.shape[0], sampling_rate):
            for x in range(0, pxl_arr.shape[1], sampling_rate):
                pixel = tuple(pxl_arr[y, x])

                pixel_traversed += 1
                
                color_dict[pixel] = 1 if pixel not in color_dict else color_dict[pixel] + 1

        # print(pxl_arr.shape)
        # img.show()

        color_trackers = []
        for color, freq in color_dict.items():

            # If list is unpopulated
            if not color_trackers:
                color_trackers.append(
                    ColorTracker(color=color, weight=freq)
                )
            # Otherwise check existing colors
            else:
                # Go through stored color and add to existing if close enough
                for ct in color_trackers:
                    if df(color, ct.color) <= color_sep:
                        # ct.avg_add(color, multiplicity=freq)
                        gm(ct, color, multiplicity=freq)
                        break
                # If finished without finding a kin, new entry
                else:
                    color_trackers.append(
                        ColorTracker(color=color, weight=freq)
                    )

        print(f'Distinct hex: {len(color_dict)}')
        print(f'Initial palette: {len(color_trackers)}')

        # Sort by value (light or dark)
        color_trackers.sort(key=lambda ct: -int(get_hsv(ct)[2])) # sort by 0=hue, 1=saturation, 2=value
        
        len_ct_lst = len(color_trackers)
        idx_0, idx_1, idx_2, idx_3 = 0, (len_ct_lst * 1) // 3, (len_ct_lst * 2) // 3, len_ct_lst

        # Bucket by value and sort by saturation
        light = sorted(color_trackers[idx_0:idx_1], key=lambda ct: get_hsv(ct)[1])
        mid = sorted(color_trackers[idx_1:idx_2], key=lambda ct: get_hsv(ct)[1])
        dark = sorted(color_trackers[idx_2:idx_3], key=lambda ct: get_hsv(ct)[1])

        # sort_func = lambda ct: ct.weight
        sort_func = lambda ct: get_hsv(ct)[0]
        light_desat = sorted(unify_palette(light[:len(light)//2]), key=sort_func)
        light_sat = sorted(unify_palette(light[len(light)//2:]), key=sort_func)
        mid_desat = sorted(unify_palette(mid[:len(mid)//2]), key=sort_func)
        mid_sat = sorted(unify_palette(mid[len(mid)//2:]), key=sort_func)
        dark_desat = sorted(unify_palette(dark[:len(dark)//2]), key=sort_func)
        dark_sat = sorted(unify_palette(dark[len(dark)//2:]), key=sort_func)

        for bucket, palette in [
            ['Light & Saturated', light_sat],
            ['Light & Desaturated', light_desat],
            ['Medium & Saturated', mid_sat],
            ['Medium & Desaturated', mid_desat],
            ['Dark & Saturated', dark_sat],
            ['Dark & Desaturated', dark_desat],
        ]:
            print(bucket, 'Weight:',sum(ct.weight for ct in palette))
            show_palette(palette)




if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='A program that will take an image file as input and output a color scheme.')

    parser.add_argument('--input_file', '-if', type=str, required=True, help='Path to the input file.')
    parser.add_argument('--minimum_color_separation', '-m', type=int, default=32, help='How far should each color in palette be separated by?')
    parser.add_argument('--sampling', '-s', type=int, default=16, help='How frequently will pixel be read.')
    parser.add_argument('--num_colors', '-n', type=int, default=12, help='Number of colors in the output.')
    parser.add_argument(
        '--distance_function', '-df',
        type=str, choices=['naive', 'rrm'], default='rrm',
        help='How to evaluate chroma distance. Naive is just the rectlinear distance in RGB space. RRM is like Naive, but adjusts for perceptual weight of each channel.'
        )
    parser.add_argument(
        '--grouping_method', '-gm',
        type=str, choices=['avg', 'rpr'], default='rpr',
        help='How to choose new color of group. Avg is average and rpr is representative (no mixing).'
        )

    args = parser.parse_args()

    infer_color_palette(
        args.input_file,
        args.sampling,
        args.num_colors,
        args.minimum_color_separation,
        args.distance_function,
        args.grouping_method,
        )

