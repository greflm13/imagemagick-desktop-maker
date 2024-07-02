#!/bin/bash

RED='\033[0;31m'    #'0;31' is Red
GREEN='\033[0;32m'  #'0;32' is Green
YELLOW='\033[1;33m' #'1;33' is Yellow
BLUE='\033[0;34m'   #'0;34' is Blue
NONE='\033[0m'      # NO COLOR

wallpaperdir="Wallpapers"
svgdir="Svgs"
outdir="Render"

tmppath="/tmp/wallpapermaker"
mkdir -p "$tmppath"

blur() {
    #  ____  _
    # | __ )| |_   _ _ __
    # |  _ \| | | | | '__|
    # | |_) | | |_| | |
    # |____/|_|\__,_|_|
    #

    local input_image output_image temp_shadow_over method

    method="Blur"
    input_image="$1"
    in_file="${input_image/$wallpaperdir\//}"
    output_image="$3/$method/$logo_name/$in_file"

    mkdir -p "$3/$method/$logo_name"

    if [ ! -f "$output_image" ]; then
        # Temporary files
        temp_shadow_over="${tmppath}/${method}_${logo_name}_temp_shadow_over.jpg"

        echo -e "${GREEN}${logo_name} ${method} ${BLUE}Step 9${NONE}: Add Shadow to background"
        magick "$temp_blurred_dark" "$temp_shadow" -compose multiply -composite "$temp_shadow_over"

        echo -e "${GREEN}${logo_name} ${method} ${BLUE}Step 10${NONE}: Composite the brightened foreground with the darkened background using the mask"
        magick "$temp_brightened" "$temp_shadow_over" "$temp_mask" -compose over -composite "$output_image"

        echo -e "${GREEN}Output saved to ${RED}$output_image${NONE}"

        # Clean up temporary files
        rm -rf "$temp_shadow_over"
    fi
}

negate() {
    #  _   _                  _
    # | \ | | ___  __ _  __ _| |_ ___
    # |  \| |/ _ \/ _` |/ _` | __/ _ \
    # | |\  |  __/ (_| | (_| | ||  __/
    # |_| \_|\___|\__, |\__,_|\__\___|
    #             |___/

    local input_image output_image method

    method="Negate"
    input_image="$1"
    in_file="${input_image/$wallpaperdir\//}"
    output_image="$3/$method/$logo_name/$in_file"

    mkdir -p "$3/$method/$logo_name"

    if [ ! -f "$output_image" ]; then
        echo -e "${GREEN}${logo_name} ${method} ${BLUE}Step 9${NONE}: Composite the negated foreground with the background using the mask"
        magick "$temp_negated" "$input_image" "$temp_mask" -compose over -composite "$output_image"

        echo -e "${GREEN}Output saved to ${RED}$output_image${NONE}"
    fi
}

flip() {
    #  _____ _ _
    # |  ___| (_)_ __
    # | |_  | | | '_ \
    # |  _| | | | |_) |
    # |_|   |_|_| .__/
    #           |_|

    local input_image output_image temp_shadow_over method

    method="Flip"
    input_image="$1"
    in_file="${input_image/$wallpaperdir\//}"
    output_image="$3/$method/$logo_name/$in_file"

    mkdir -p "$3/$method/$logo_name"

    if [ ! -f "$output_image" ]; then
        # Temporary files
        temp_shadow_over="${tmppath}/${method}_${logo_name}_temp_shadow_over.jpg"

        echo -e "${GREEN}${logo_name} ${method} ${BLUE}Step 9${NONE}: Add Shadow to background"
        magick "$input_image" "$temp_shadow" -compose multiply -composite "$temp_shadow_over"

        echo -e "${GREEN}${logo_name} ${method} ${BLUE}Step 10${NONE}: Composite the flipped foreground with the background using the mask"
        magick "$temp_flipped" "$temp_shadow_over" "$temp_mask" -compose over -composite "$output_image"

        echo -e "${GREEN}Output saved to ${RED}$output_image${NONE}"

        # Clean up temporary files
        rm -rf "$temp_shadow_over"
    fi
}

inverseblur() {
    #  ___                              ____  _
    # |_ _|_ ____   _____ _ __ ___  ___| __ )| |_   _ _ __
    #  | || '_ \ \ / / _ \ '__/ __|/ _ \  _ \| | | | | '__|
    #  | || | | \ V /  __/ |  \__ \  __/ |_) | | |_| | |
    # |___|_| |_|\_/ \___|_|  |___/\___|____/|_|\__,_|_|
    #

    local input_image output_image temp_shadow_over method

    method="InverseBlur"
    input_image="$1"
    in_file="${input_image/$wallpaperdir\//}"
    output_image="$3/$method/$logo_name/$in_file"

    mkdir -p "$3/$method/$logo_name"

    if [ ! -f "$output_image" ]; then
        # Temporary files
        temp_shadow_over="${tmppath}/${method}_${logo_name}_temp_shadow_over.jpg"

        echo -e "${GREEN}${logo_name} ${method} ${BLUE}Step 9${NONE}: Add Shadow to background"
        magick "$input_image" "$temp_shadow" -compose multiply -composite "$temp_shadow_over"

        echo -e "${GREEN}${logo_name} ${method} ${BLUE}Step 10${NONE}: Composite the darkened foreground with the background using the mask"
        magick "$temp_blurred_dark" "$temp_shadow_over" "$temp_mask" -compose over -composite "$output_image"

        echo -e "${GREEN}Output saved to ${RED}$output_image${NONE}"

        # Clean up temporary files
        rm -rf "$temp_shadow_over"
    fi
}

inverseblurdarker() {
    #  ___                              ____  _            ____             _
    # |_ _|_ ____   _____ _ __ ___  ___| __ )| |_   _ _ __|  _ \  __ _ _ __| | _____ _ __
    #  | || '_ \ \ / / _ \ '__/ __|/ _ \  _ \| | | | | '__| | | |/ _` | '__| |/ / _ \ '__|
    #  | || | | \ V /  __/ |  \__ \  __/ |_) | | |_| | |  | |_| | (_| | |  |   <  __/ |
    # |___|_| |_|\_/ \___|_|  |___/\___|____/|_|\__,_|_|  |____/ \__,_|_|  |_|\_\___|_|
    #

    local input_image output_image temp_shadow_over method

    method="InverseBlurDarker"
    input_image="$1"
    in_file="${input_image/$wallpaperdir\//}"
    output_image="$3/$method/$logo_name/$in_file"

    mkdir -p "$3/$method/$logo_name"

    if [ ! -f "$output_image" ]; then
        # Temporary files
        temp_shadow_over="${tmppath}/${method}_${logo_name}_temp_shadow_over.jpg"

        echo -e "${GREEN}${logo_name} ${method} ${BLUE}Step 9${NONE}: Add Shadow to background"
        magick "$input_image" "$temp_shadow" -compose multiply -composite "$temp_shadow_over"

        echo -e "${GREEN}${logo_name} ${method} ${BLUE}Step 10${NONE}: Composite the darkened foreground with the background using the mask"
        magick "$temp_blurred_darker" "$temp_shadow_over" "$temp_mask" -compose over -composite "$output_image"

        echo -e "${GREEN}Output saved to ${RED}$output_image${NONE}"

        # Clean up temporary files
        rm -rf "$temp_shadow_over"
    fi
}

blackoverlay() {
    #  ____  _            _     ___                 _
    # | __ )| | __ _  ___| | __/ _ \__   _____ _ __| | __ _ _   _
    # |  _ \| |/ _` |/ __| |/ / | | \ \ / / _ \ '__| |/ _` | | | |
    # | |_) | | (_| | (__|   <| |_| |\ V /  __/ |  | | (_| | |_| |
    # |____/|_|\__,_|\___|_|\_\\___/  \_/ \___|_|  |_|\__,_|\__, |
    #                                                       |___/

    local input_image output_image temp_shadow_over method

    method="BlackOverlay"
    input_image="$1"
    in_file="${input_image/$wallpaperdir\//}"
    output_image="$3/$method/$logo_name/$in_file"

    mkdir -p "$3/$method/$logo_name"

    if [ ! -f "$output_image" ]; then
        # Temporary files
        temp_shadow_over="${tmppath}/${method}_${logo_name}_temp_shadow_over.jpg"

        echo -e "${GREEN}${logo_name} ${method} ${BLUE}Step 9${NONE}: Add Shadow to background"
        magick "$input_image" "$temp_shadow" -compose multiply -composite "$temp_shadow_over"

        echo -e "${GREEN}${logo_name} ${method} ${BLUE}Step 10${NONE}: Composite the black foreground with the background using the mask"
        magick -size "${input_width}x${input_height}" xc:black "$temp_shadow_over" "$temp_mask" -compose over -composite "$output_image"

        echo -e "${GREEN}Output saved to ${RED}$output_image${NONE}"

        # Clean up temporary files
        rm -rf "$temp_shadow_over"
    fi
}

whiteoverlay() {
    # __        ___     _ _        ___                 _
    # \ \      / / |__ (_) |_ ___ / _ \__   _____ _ __| | __ _ _   _
    #  \ \ /\ / /| '_ \| | __/ _ \ | | \ \ / / _ \ '__| |/ _` | | | |
    #   \ V  V / | | | | | ||  __/ |_| |\ V /  __/ |  | | (_| | |_| |
    #    \_/\_/  |_| |_|_|\__\___|\___/  \_/ \___|_|  |_|\__,_|\__, |
    #                                                          |___/

    local input_image output_image temp_shadow_over method

    method="WhiteOverlay"
    input_image="$1"
    in_file="${input_image/$wallpaperdir\//}"
    output_image="$3/$method/$logo_name/$in_file"

    mkdir -p "$3/$method/$logo_name"

    if [ ! -f "$output_image" ]; then
        # Temporary files
        temp_shadow_over="${tmppath}/${method}_${logo_name}_temp_shadow_over.jpg"

        echo -e "${GREEN}${logo_name} ${method} ${BLUE}Step 9${NONE}: Add Shadow to background"
        magick "$input_image" "$temp_shadow" -compose multiply -composite "$temp_shadow_over"

        echo -e "${GREEN}${logo_name} ${method} ${BLUE}Step 10${NONE}: Composite the white foreground with the background using the mask"
        magick -size "${input_width}x${input_height}" xc:white "$temp_shadow_over" "$temp_mask" -compose over -composite "$output_image"

        echo -e "${GREEN}Output saved to ${RED}$output_image${NONE}"

        # Clean up temporary files
        rm -rf "$temp_shadow_over"
    fi
}

throughblack() {
    #  _____ _                           _     ____  _            _
    # |_   _| |__  _ __ ___  _   _  __ _| |__ | __ )| | __ _  ___| | __
    #   | | | '_ \| '__/ _ \| | | |/ _` | '_ \|  _ \| |/ _` |/ __| |/ /
    #   | | | | | | | | (_) | |_| | (_| | | | | |_) | | (_| | (__|   <
    #   |_| |_| |_|_|  \___/ \__,_|\__, |_| |_|____/|_|\__,_|\___|_|\_\
    #                              |___/

    local input_image output_image method

    method="ThroughBlack"
    input_image="$1"
    in_file="${input_image/$wallpaperdir\//}"
    output_image="$3/$method/$logo_name/$in_file"

    mkdir -p "$3/$method/$logo_name"

    if [ ! -f "$output_image" ]; then
        echo -e "${GREEN}${logo_name} ${method} ${BLUE}Step 9${NONE}: Composite the foreground with the black background using the mask"
        magick "$input_image" -size "${input_width}x${input_height}" xc:black "$temp_mask" -compose over -composite "$output_image"

        echo -e "${GREEN}Output saved to ${RED}$output_image${NONE}"
    fi
}

pixelate() {
    #  ____  _          _       _
    # |  _ \(_)_  _____| | __ _| |_ ___
    # | |_) | \ \/ / _ \ |/ _` | __/ _ \
    # |  __/| |>  <  __/ | (_| | ||  __/
    # |_|   |_/_/\_\___|_|\__,_|\__\___|
    #

    local input_image output_image method

    method="Pixelate"
    input_image="$1"
    in_file="${input_image/$wallpaperdir\//}"
    output_image="$3/$method/$logo_name/$in_file"

    mkdir -p "$3/$method/$logo_name"

    if [ ! -f "$output_image" ]; then
        echo -e "${GREEN}${logo_name} ${method} ${BLUE}Step 9${NONE}: Composite the foreground with the pixelated background using the mask"
        magick "$input_image" "$temp_pixelated" "$temp_mask" -compose over -composite "$output_image"

        echo -e "${GREEN}Output saved to ${RED}$output_image${NONE}"
    fi

}

inversenegate() {
    #  ___                              _   _                  _
    # |_ _|_ ____   _____ _ __ ___  ___| \ | | ___  __ _  __ _| |_ ___
    #  | || '_ \ \ / / _ \ '__/ __|/ _ \  \| |/ _ \/ _` |/ _` | __/ _ \
    #  | || | | \ V /  __/ |  \__ \  __/ |\  |  __/ (_| | (_| | ||  __/
    # |___|_| |_|\_/ \___|_|  |___/\___|_| \_|\___|\__, |\__,_|\__\___|
    #                                              |___/

    local input_image output_image method

    method="InverseNegate"
    input_image="$1"
    in_file="${input_image/$wallpaperdir\//}"
    output_image="$3/$method/$logo_name/$in_file"

    mkdir -p "$3/$method/$logo_name"

    if [ ! -f "$output_image" ]; then
        echo -e "${GREEN}${logo_name} ${method} ${BLUE}Step 9${NONE}: Composite the negated background with the foreground using the mask"
        magick "$input_image" "$temp_negated" "$temp_mask" -compose over -composite "$output_image"

        echo -e "${GREEN}Output saved to ${RED}$output_image${NONE}"
    fi
}

render() {
    methods=(Blur Negate InverseNegate Flip InverseBlur InverseBlurDarker BlackOverlay WhiteOverlay ThroughBlack Pixelate)
    input_image="$1"
    in_file="${input_image/$wallpaperdir\//}"
    in_name="${in_file%.jpg}"
    logo_name="$(echo "$2" | sed "s/$svgdir\///g;s/.svg//g")"

    temp_mask="${tmppath}/${logo_name}_temp_mask.png"
    temp_shadow="${tmppath}/${logo_name}_temp_shadow.jpg"
    temp_blurred_dark="${tmppath}/${in_name}_temp_blurred_dark.jpg"
    temp_blurred_darker="${tmppath}/${in_name}_temp_blurred_darker.jpg"
    temp_brightened="${tmppath}/${in_name}_temp_brightened.jpg"
    temp_negated="${tmppath}/${in_name}_temp_negated.jpg"
    temp_flipped="${tmppath}/${in_name}_temp_flipped.jpg"
    temp_pixelated="${tmppath}/${in_name}_temp_pixelated.jpg"

    rendering=false

    for method in "${methods[@]}"; do
        output_image="$3/$method/$logo_name/$in_file"
        if [ ! -f "$output_image" ]; then
            rendering=true
        fi
    done

    if $rendering; then
        echo -e "${YELLOW}${logo_name}/${in_file}${NONE}"

        echo -e "${GREEN}${logo_name} ${BLUE}Step 1${NONE}: Get dimensions of the input image"
        input_width=$(magick identify -format "%w" "$1")
        input_height=$(magick identify -format "%h" "$1")

        if [ ! -f "$temp_mask" ]; then
            echo -e "${GREEN}${logo_name} ${BLUE}Step 2${NONE}: Convert the SVG mask to a PNG (not existing)"
            magick "$2" -resize "${input_width}x${input_height}" "$temp_mask"
        else
            mask_height=$(magick identify -format "%h" "$temp_mask")
            if [ "$input_height" != "$mask_height" ]; then
                echo -e "${GREEN}${logo_name} ${BLUE}Step 2${NONE}: Convert the SVG mask to a PNG (wrong size)"
                magick "$2" -resize "${input_width}x${input_height}" "$temp_mask"
            fi
        fi

        if [ ! -f "$temp_shadow" ]; then
            echo -e "${GREEN}${logo_name} ${BLUE}Step 3${NONE}: Blur the mask to get a shadow (not existing)"
            magick "$temp_mask" -blur 100x50 "$temp_shadow" &
        elif [ "$input_height" != "$mask_height" ]; then
            echo -e "${GREEN}${logo_name} ${BLUE}Step 3${NONE}: Blur the mask to get a shadow (wrong size)"
            magick "$temp_mask" -blur 100x50 "$temp_shadow" &
        fi

        if [ ! -f "$temp_blurred_dark" ]; then
            echo -e "${GREEN}${logo_name} ${BLUE}Step 4${NONE}: Blur and darken the original image"
            magick "$input_image" -define modulate:colorspace=HSB -modulate 80 -blur 80x40 "$temp_blurred_dark" &
        fi

        if [ ! -f "$temp_blurred_darker" ]; then
            echo -e "${GREEN}${logo_name} ${BLUE}Step 5${NONE}: Blur and darken the original image more"
            magick "$input_image" -define modulate:colorspace=HSB -modulate 40 -blur 80x40 "$temp_blurred_darker" &
        fi

        if [ ! -f "$temp_brightened" ]; then
            echo -e "${GREEN}${logo_name} ${BLUE}Step 5${NONE}: Brighten the original image"
            magick "$input_image" -define modulate:colorspace=HSB -modulate 110 "$temp_brightened" &
        fi

        if [ ! -f "$temp_negated" ]; then
            echo -e "${GREEN}${logo_name} ${BLUE}Step 6${NONE}: Negate the original image" &
            magick "$input_image" -negate "$temp_negated"
        fi

        if [ ! -f "$temp_flipped" ]; then
            echo -e "${GREEN}${logo_name} ${BLUE}Step 9${NONE}: Flip the original image"
            magick "$input_image" -flip "$temp_flipped" &
        fi

        if [ ! -f "$temp_pixelated" ]; then
            echo -e "${GREEN}${logo_name} ${BLUE}Step 8${NONE}: Pixelate the original image"
            magick "$input_image" -define modulate:colorspace=HSB -modulate 80 -scale 1% -scale 10000% "$temp_pixelated" &
        fi

        wait

        blur "$@" &
        negate "$@" &
        inversenegate "$@" &
        flip "$@" &
        inverseblur "$@" &
        inverseblurdarker "$@" &
        blackoverlay "$@" &
        whiteoverlay "$@" &
        throughblack "$@" &
        pixelate "$@" &
    fi
}

main() {
    for wallpaper in "$wallpaperdir"/*; do
        for svg in "$svgdir"/*.svg; do
            render "$wallpaper" "$svg" "$outdir"
            wait
        done
    done

    # Clean up temporary files
    rm -rf "${tmppath}"
}

main "$@"
