# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import print_function
import re
import difflib

from django.utils.safestring import mark_safe


__all__ = (
    'get_compare_title',
)


def display_diff(css_class, diff_list):
    """
    suround every item of diff_list with <span> using provided CSS class
    """
    if not diff_list:
        return ''
    response = ''
    for d in diff_list:
        response += '<span class="%s">' % css_class + d + '</span>' + '.'
    return response[:-1]


def get_compare_title(nvr, base_nvr):
    """
    compare two NVRs, mark different parts with <span>
    """
    re_nvr = re.match("(.*)-(.*)-(.*)", nvr)
    re_base = re.match("(.*)-(.*)-(.*)", base_nvr)
    outer_index = 1  # firstly compare version, then release
    inner_index = 0  # hop over all version numbers
    result_nvr = ''
    result_base = ''
    diff_found = False
    while True:
        try:
            nvr_numbers = re_nvr.group(outer_index).split('.')
        except IndexError:
            break
        base_numbers = re_base.group(outer_index).split('.')
        # mark rest if diff was already found
        if diff_found:
            result_nvr += display_diff('light_green_font', nvr_numbers)
            result_base += display_diff('red_font', base_numbers)
        else:
            while True:
                try:
                    # compare current part
                    condition = nvr_numbers[inner_index] == \
                        base_numbers[inner_index]
                except IndexError:
                    # we are out of index:
                    # - this might be due to fact that we processed last item
                    # - or that lists have different count of items
                    if len(nvr_numbers) != len(base_numbers):
                        diff_found = True
                        try:
                            result_nvr += display_diff(
                                'light_green_font',
                                nvr_numbers[inner_index:len(nvr_numbers)])
                        except IndexError:
                            pass
                        try:
                            result_base += display_diff(
                                'red_font',
                                base_numbers[inner_index:len(base_numbers)])
                        except IndexError:
                            pass
                    if result_nvr.endswith('.'):
                        result_nvr = result_nvr[:-1]
                    if result_base.endswith('.'):
                        result_base = result_base[:-1]
                    inner_index = 0
                    break
                if condition:
                    # condition holds, diff wasn't found yet
                    result_nvr += nvr_numbers[inner_index] + '.'
                    result_base += base_numbers[inner_index] + '.'
                else:
                    # we have found diff, mark rest
                    diff_found = True
                    result_nvr += display_diff('light_green_font',
                                               nvr_numbers[inner_index:],)
                    result_base += display_diff('red_font',
                                                base_numbers[inner_index:])
                    break
                inner_index += 1
        result_nvr += '-'
        result_base += '-'
        outer_index += 1
    if result_nvr.endswith('-'):
        result_nvr = result_nvr[:-1]
    if result_base.endswith('-'):
        result_base = result_base[:-1]
    return mark_safe(result_nvr + ' compared to ' + result_base)


def get_compare_title_re(nvr, base_nvr):
    """
    Different implementation of comparison using re
    """
    re_nvr = re.match("(.*)-(.*)-(.*)", nvr)
    re_base = re.match("(.*)-(.*)-(.*)", base_nvr)
    outer_index = 1
    inner_index = 0
    result_nvr = ''
    result_base = ''
    while True:
        try:
            nvr_numbers = re_nvr.group(outer_index).split('.')
        except IndexError:
            break
        base_numbers = re_base.group(outer_index).split('.')
        print(nvr_numbers, base_numbers)
        while True:
            try:
                condition = nvr_numbers[inner_index] == \
                    base_numbers[inner_index]
            except IndexError:
                if max(len(nvr_numbers), len(base_numbers)) != inner_index:
                    try:
                        result_nvr += '.'.join(nvr_numbers[inner_index:len(nvr_numbers)])
                    except IndexError:
                        pass
                    try:
                        result_base += '.'.join(base_numbers[inner_index:len(base_numbers)])
                    except IndexError:
                        pass
                if result_nvr.endswith('.'): result_nvr = result_nvr[:-1]
                if result_base.endswith('.'): result_base = result_base[:-1]
                inner_index = 0
                break
            if condition:
                result_nvr += nvr_numbers[inner_index] + '.'
                result_base += base_numbers[inner_index] + '.'
            else:
                result_nvr += '<span class="result_target_nvr">%s</span>.'\
                    % nvr_numbers[inner_index]
                result_base += '<span class="result_base_nvr">%s</span>.'\
                    % base_numbers[inner_index]
            inner_index += 1
        result_nvr += '-'
        result_base += '-'
        outer_index += 1
    if result_nvr.endswith('-'): result_nvr = result_nvr[:-1]
    if result_base.endswith('-'): result_base = result_base[:-1]
    return mark_safe(result_nvr + ' compared to ' + result_base)


def get_compare_title_difflib(nvr, base_nvr):
    """
    implementation that uses difflib
    """
    blocks = difflib.SequenceMatcher(a=nvr, b=base_nvr,
                                     autojunk=False).get_matching_blocks()
    print(nvr, base_nvr)
    print(blocks)
    i = 0
    offset = 0
    result_nvr = ''
    result_base = ''
    diff_active = False

    while True:
        if blocks[i][2] == 0:
            if offset != max(len(nvr), len(base_nvr)):
                result_nvr += nvr[offset:len(nvr)]
                result_base += base_nvr[offset:len(base_nvr)]
            if diff_active:
                result_nvr += '</span>'
                result_base += '</span>'
            break

        if diff_active:
            result_nvr += nvr[offset:blocks[i][0]] + '</span>'
            result_base += base_nvr[offset:blocks[i][1]] + '</span>'
            offset += min(blocks[i][0]-offset, blocks[i][1]-offset)
        else:
            result_nvr += nvr[blocks[i][0]:blocks[i][2]+offset]
            result_base += base_nvr[blocks[i][1]:blocks[i][2]+offset]
            if blocks[i+1][2] != 0:
                result_nvr += '<span class="result_target_nvr">'
                result_base += '<span class="result_base_nvr">'
            offset += blocks[i][2]
            i += 1
        diff_active ^= True  # alternate

    return mark_safe(result_nvr + ' compared to ' + result_base)


def get_display_diff_sequences(seq1, seq2):
    blocks = difflib.SequenceMatcher(a=seq1, b=seq2,
                                     autojunk=True).get_matching_blocks()
    i = 0
    seq1_offset = 0
    seq2_offset = 0
    result_seq1 = ''
    result_seq2 = ''
    if blocks[0][0] != 0 or blocks[0][1] != 0:
        diff_active = True
    else:
        diff_active = False
    while True:
        if diff_active:
            result_seq1 += display_diff('result_target_nvr', seq1[seq1_offset:blocks[i][0]])
            result_seq2 += display_diff('result_base_nvr', seq2[seq2_offset:blocks[i][1]])
            seq1_offset += blocks[i][0]
            seq2_offset += blocks[i][1]
        else:
            result_seq1 += '.'.join(seq1[blocks[i][0]:blocks[i][2] + seq1_offset]) + '.'
            result_seq2 += '.'.join(seq2[blocks[i][1]:blocks[i][2] + seq2_offset]) + '.'

            seq1_offset += blocks[i][2]
            seq2_offset += blocks[i][2]
            i += 1
        diff_active ^= True
        if blocks[i][2] == 0:
            if diff_active:
                if seq1_offset < len(seq1):
                    result_seq1 += display_diff('result_target_nvr',
                                                seq1[seq1_offset:len(seq1)])
                if seq2_offset < len(seq2):
                    result_seq2 += display_diff('result_base_nvr',
                                                seq2[seq2_offset:len(seq2)])
            else:
                if seq1_offset < len(seq1):
                    result_seq1 += '.'.join(seq1[seq1_offset:len(seq1)])
                if seq2_offset < len(seq2):
                    result_seq2 += '.'.join(seq2[seq2_offset:len(seq2)])
            break
    if result_seq1.endswith('.'):
        result_seq1 = result_seq1[:-1]
    if result_seq2.endswith('.'):
        result_seq2 = result_seq2[:-1]
    return result_seq1, result_seq2


def get_compare_title_re2(nvr, base_nvr):
    """
    yet another implementation
    """
    re_nvr = re.match("(.*)-(.*)-(.*)", nvr)
    re_base = re.match("(.*)-(.*)-(.*)", base_nvr)
    outer_index = 1
    result_nvr = ''
    result_base = ''
    while True:
        try:
            nvr_numbers = re_nvr.group(outer_index).split('.')
        except IndexError:
            break
        base_numbers = re_base.group(outer_index).split('.')
        tmp_nvr, tmp_base = get_display_diff_sequences(nvr_numbers,
                                                       base_numbers)
        result_nvr += tmp_nvr + '-'
        result_base += tmp_base + '-'
        outer_index += 1
    if result_nvr.endswith('-'):
        result_nvr = result_nvr[:-1]
    if result_base.endswith('-'):
        result_base = result_base[:-1]
    return mark_safe(result_nvr + ' compared to ' + result_base)