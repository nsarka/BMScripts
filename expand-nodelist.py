#!/usr/bin/env python3
import sys

def parse_string_range(input_str, suffix_num=None):
    """
    Parse strings with format "prefix[range]" where range can include:
    - Hyphenated ranges (e.g., 03-07)
    - Individual numbers (e.g., 09)
    - Combinations of both separated by commas
    Optional suffix in format ":X" can be added to each value

    Args:
        input_str (str): Input string in format "prefix[range]"
        suffix_num (int, optional): If provided, adds ":suffix_num" to each value

    Returns:
        str: Comma-separated string of expanded values

    Examples:
        >>> parse_string_range("rock[03-07,09,16,24]")
        'rock03,rock04,rock05,rock06,rock07,rock09,rock16,rock24'
        >>> parse_string_range("rock[03-07,09,16,24]", suffix_num=1)
        'rock03:1,rock04:1,rock05:1,rock06:1,rock07:1,rock09:1,rock16:1,rock24:1'
    """
    # Split into prefix and range parts
    prefix = input_str[:input_str.find('[')]
    range_part = input_str[input_str.find('[')+1:input_str.find(']')]

    # Split range part by commas
    range_segments = range_part.split(',')

    result = []
    for segment in range_segments:
        if '-' in segment:
            # Handle range (e.g., 03-07)
            start, end = segment.split('-')
            # Convert to int to handle leading zeros properly
            start_num = int(start)
            end_num = int(end)
            # Generate range with proper zero padding
            for num in range(start_num, end_num + 1):
                base_value = f"{prefix}{str(num).zfill(len(start))}"
                if suffix_num is not None:
                    base_value += f":{suffix_num}"
                result.append(base_value)
        else:
            # Handle individual numbers
            base_value = f"{prefix}{segment}"
            if suffix_num is not None:
                base_value += f":{suffix_num}"
            result.append(base_value)

    return ','.join(result)

if __name__ == '__main__':
    if len(sys.argv) == 3:
        print(parse_string_range(sys.argv[1], sys.argv[2]))
    elif len(sys.argv) == 2:
        print(parse_string_range(sys.argv[1], None))
    else:
        print("Usage:", sys.argv[0], "nodelist_string <PPN>")

