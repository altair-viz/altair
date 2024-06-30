.. currentmodule:: altair

.. _user-guide-color:

Color Usage
===========

Effective visualization of scientific data requires careful attention
to color selection. Choosing the right colors can be a complex task,
involving considerations such as color perception, accessibility,
and aesthetics. Fortunately, there are a number of resources available
to help simplify this process, including pre-designed color schemes
and tools for exploring and modifying color scales. In this guide,
we'll explore some of the basics of color selection for scientific 
data visualization, including different types of color scales and
examples of their use.

.. altair-plot::
    :remove-code:
    :output: none

    import altair as alt
    from vega_datasets import data
    import pandas as pd

    def chart_settings(scheme_name, dict_schemes, continuous):
        # check if the input is a defined or custom scheme
        custom_scheme = True if type(dict_schemes[scheme_name]) is list else False

        # define a data sequence of 300 for continuous color schemes
        if continuous:
            no_colors = continuous if type(continuous) is int else 300
            data = alt.sequence(0, no_colors, as_="i")

        # define a data sequence using dict for defined schemes
        elif type(dict_schemes[scheme_name]) is int:
            no_colors = dict_schemes[scheme_name]
            data = alt.sequence(0, no_colors, as_="i")

        # define a dataframe for custom schemes (possible with Altair only?)
        else:
            no_colors = len(dict_schemes[scheme_name])
            colors_in_scheme = dict_schemes[scheme_name]
            data = pd.DataFrame({"i": range(no_colors), "hex": colors_in_scheme})

        # dynamic width
        max_width = 400
        w = max_width / no_colors

        # cornerRadius dependent on height-width ratio
        cr_l = 0 if continuous else 10
        cr_s = 0 if continuous else 5

        return {
            "data": data,
            "width": w,
            "cornerRadius_large": cr_l,
            "cornerRadius_small": cr_s,
            "no_colors": no_colors,
            "custom": custom_scheme
        }

    def chart_color_scale(scheme_name, dict_schemes, continuous, custom, no, method):
        color_type = "quantitative" if custom and continuous else "ordinal"    
        scale_scheme = alt.Scale(range=dict_schemes[scheme_name]) if custom else alt.Scale(scheme=scheme_name)
        scale_scheme.interpolate = method

        color_scale = (
            alt.Chart(alt.sequence(0, no, as_="i"))
            .mark_rect(height=alt.expr("0"), width=alt.expr("0"))
            .encode(alt.Color("i", type=color_type).scale(scale_scheme).legend(None))
        )    

        return color_scale

    def chart_normal_vision(data, h, w, expr_hex, my_y_axis, cr_l, no):
        stroke_nv = alt.value('gray') if no < 25 else alt.Stroke("hex_raw:N").scale(None).legend(None)
        normal_vision = (
            alt.Chart(data, height=h, width=alt.Step(w))
            .transform_calculate(
                hex_raw=expr_hex,
                rgb="rgb(datum.hex_raw)",
                lum="luminance(datum.hex_raw)",
                hex="'#'+format(datum.rgb['r'], '02x')+format(datum.rgb['g'], '02x')+format(datum.rgb['b'], '02x')"
            )
            .mark_rect(cornerRadius=cr_l)
            .encode(
                x=alt.X("i:O").axis(None),
                y=alt.Y("normal vision:O").axis(my_y_axis),
                fill=alt.Fill("hex_raw:O").scale(None).legend(None),
                stroke=stroke_nv,
                tooltip=[
                    alt.Tooltip("hex:O"),
                    alt.Tooltip("rgb:O"),
                    alt.Tooltip("lum:O", format=".2"),
                ],
            )
        )
        return normal_vision

    def chart_green_blindness(data, h, w, expr_hex, my_y_axis, cr_s, no):
        stroke_gb = alt.value('gray') if no < 25 else alt.Stroke("greenblind_rgb:N").scale(None).legend(None)
        green_blindness = (
            alt.Chart(data, height=h, width=alt.Step(w))
            .transform_calculate(
                hex=expr_hex,
                rgb="rgb(datum.hex)",
                gb_r="pow((4211+0.667*pow(datum.rgb['g'], 2.2)+0.2802*pow(datum.rgb['r'], 2.2)),1/2.2)",
                gb_g="pow((4211+0.667*pow(datum.rgb['g'], 2.2)+0.2802*pow(datum.rgb['r'], 2.2)),1/2.2)",
                gb_b="pow((4211+0.95724*pow(datum.rgb['b'], 2.2)+0.02138*pow(datum.rgb['b'], 2.2)-0.02138*pow(datum.rgb['r'], 2.2)),1/2.2)",
                greenblind_rgb="rgb(datum.gb_r,datum.gb_g,datum.gb_b)",
            )
            .mark_rect(cornerRadius=cr_s)
            .encode(
                x=alt.X("i:O").axis(None),
                y=alt.Y("green-blindness:N").axis(my_y_axis),
                fill=alt.Fill("greenblind_rgb:N").scale(None).legend(None),
                stroke=stroke_gb           
            )
        )    
        return green_blindness

    def chart_red_blindness(data, h, w, expr_hex, my_y_axis, cr_s, no):
        stroke_rb = alt.value('gray') if no < 25 else alt.Stroke("redblind_rgb:N").scale(None).legend(None)
        red_blindness = (
            alt.Chart(data, height=h, width=alt.Step(w))
            .transform_calculate(
                hex=expr_hex,
                rgb="rgb(datum.hex)",
                rb_r="pow((782.7+0.8806*pow(datum.rgb['g'], 2.2)+0.1115*pow(datum.rgb['r'], 2.2)),1/2.2)",
                rb_g="pow((782.7+0.8806*pow(datum.rgb['g'], 2.2)+0.1115*pow(datum.rgb['r'], 2.2)),1/2.2)",
                rb_b="pow((782.7+0.992052*pow(datum.rgb['b'], 2.2)-0.03974*pow(datum.rgb['b'], 2.2)+0.003974*pow(datum.rgb['r'], 2.2)),1/2.2)",
                redblind_rgb="rgb(datum.rb_r,datum.rb_g,datum.rb_b)",
            )
            .mark_rect(cornerRadius=cr_s)
            .encode(
                x=alt.X("i:O").axis(None),
                y=alt.Y("red-blindness:N").axis(my_y_axis),
                fill=alt.Fill("redblind_rgb:N").scale(None).legend(None),
                stroke=stroke_rb            
            )
        )  
        return red_blindness

    def chart_grayscale(data, h, w, expr_hex, my_y_axis, cr_s, no):
        stroke_gs = alt.value('gray') if no < 25 else alt.Stroke("grayscale_rgb:N").scale(None).legend(None)
        grayscale = (
            alt.Chart(data, height=h, width=alt.Step(w))
            .transform_calculate(
                hex=expr_hex,
                rgb="rgb(datum.hex)",
                lumn_rgb="datum.rgb['r']*0.3+datum.rgb['g']*0.59+datum.rgb['b']*0.3",
                grayscale_rgb="rgb(datum.lumn_rgb,datum.lumn_rgb,datum.lumn_rgb)",
            )
            .mark_rect(cornerRadius=cr_s)
            .encode(
                x=alt.X("i:O").axis(None),
                y=alt.Y("grayscale:N").axis(my_y_axis),
                fill=alt.Fill("grayscale_rgb:N").scale(None).legend(None),
                stroke=stroke_gs,               

            )
        )
        return grayscale

    def plot_scheme(scheme_name, dict_schemes, continuous=False, cvd=False, grayscale=False, top=False, bottom=False, single=True, method='rgb'):
        # determine chart settings
        chart_dict = chart_settings(scheme_name, dict_schemes, continuous)    

        # unpack chart_dict
        custom = chart_dict['custom']
        data = chart_dict['data']
        w = chart_dict['width']
        h_l = 50
        h_s = 20
        cr_l = chart_dict['cornerRadius_large']
        cr_s = chart_dict['cornerRadius_small']
        no = chart_dict['no_colors']

        # define color scale and stroke
        color_scale = chart_color_scale(scheme_name, dict_schemes, continuous, custom, no, method)

        # define how hex-codes can be derived, from datasource or using color scale
        if single:
            expr_hex = "datum.hex" if custom and not continuous else "scale('color', datum.i)"
        elif top:
            expr_hex = "datum.hex" if custom and not continuous else "scale('concat_0_color', datum.i)"
        elif bottom:
            expr_hex = "datum.hex" if custom and not continuous else "scale('concat_1_color', datum.i)"

        # define styling for y-axis
        my_y_axis = alt.Axis(
            grid=False,
            ticks=False,
            labels=False,
            domain=False,
            titleAngle=0,
            titleAlign="right",
            titleBaseline="middle",
        )    

        # determine color pallettes for different color deficiencies
        normal_vision = chart_normal_vision(data, h_l, w, expr_hex, my_y_axis, cr_l, no)
        green_blindness = chart_green_blindness(data, h_s, w, expr_hex, my_y_axis, cr_s, no)
        red_blindness = chart_red_blindness(data, h_s, w, expr_hex, my_y_axis, cr_s, no)
        monochrome = chart_grayscale(data, h_s, w, expr_hex, my_y_axis, cr_s, no)

        # determine which color pallettes to return
        if cvd and grayscale:
            chart_concat = (normal_vision & green_blindness & red_blindness & monochrome & color_scale)
        elif cvd and not grayscale:
            chart_concat = (normal_vision & green_blindness & red_blindness & color_scale)
        else:
            chart_concat = (normal_vision & color_scale)

        # set configuration on concatenated chart object
        if single:
            chart_concat = chart_concat.configure_concat(spacing=1).configure_view(stroke=None)    
        return chart_concat


The basics of color selection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Color selection is an essential aspect of creating clear and informative
visualizations of scientific data. To make the most effective choices,
it's important to understand the basics of color perception and theory.

Color perception and theory
^^^^^^^^^^^^^^^^^^^^^^^^^^^

We will explain the basics using two colors, ``blue`` and ``orange``: 
 
.. altair-plot::
    :remove-code:

    percep_schemes = {
        "two_color": ['blue','orange']
    }    
    plot_scheme("two_color", percep_schemes, cvd=False, continuous=False, method='hcl').configure_scale(rectBandPaddingInner=0.1)

Now, lets say we want to define a gradient between ``blue`` and ``orange``.
That means we have to go gradually from ``blue`` to ``orange``. 
The interpolation between colors can follow several methods.

It could be done like this (``interpolate='rgb'``):
 
.. altair-plot::
    :remove-code:
  
    plot_scheme("two_color", percep_schemes, cvd=False, continuous=300, method='rgb')

Or like this (``interpolate='hcl-long'``):
 
.. altair-plot::
    :remove-code:
  
    plot_scheme("two_color", percep_schemes, cvd=False, continuous=300, method='hcl-long')

Or like this (``interpolate='hcl'``):
 
.. altair-plot::
    :remove-code:
  
    plot_scheme("two_color", percep_schemes, cvd=False, continuous=300, method='hcl')

As you can observe, all three color ramps are different,
but all three color ramps start with ``blue`` and finish with ``orange``.

So what is the correct interpolation method to go from ``blue`` to ``orange``?
There is no single answer to this question. 
It also based how we see colors. 
To better understand the perception of colors to the human-eye, we
can make use of a color space. A color space is a diagram to help
understand how we see perceive colors and how they are distributed compare to each other.

Here we show a common used color space ('CIE 1931 color space') from where we
can see that the human eye has more attenuation to the color green:

.. altair-plot::
    :hide-code:
  
    import lzma
    import io

    compressed_df_cie1931 = b'\xfd7zXZ\x00\x00\x04\xe6\xd6\xb4F\x02\x00!\x01\x16\x00\x00\x00t/\xe5\xa3\xe10\x9e\x1dp]\x00@\x01Nm\xa9\xb6E\x9b\x19_AS\x16\xb8\xb2s\xd2\x1b\xc9\x1e\xda\xbbR\x0b\x11\x9a\x98;K\xf9\xdaH\xf5\xb8K\x08\xe47\x8e\xd3/\x80\xfc\xad\xaeQ\xc7@\x98=\xcc\x04\xb6\xc0N\xd0\x17\x10\xdd\x85d9j\xd5=\x01\xff\xdf\xfcM\x8c\x1a;r\x02\x97\xd6O\xf0(\xe7\x82\x96\xfe4\x08\xf9\xc6U}\xff\xfa,\x14#4\x93\xd2a\xc5\x18\xcb\xd16\x00Qa\xd39mx\x90\x16\xec6SV&\xfe\x86\x18,\xe1X\xa72\xd3u\x92\xe9\x10\xb6@\x0c\x87\x94\x05"\xf4N\xaa^|\xec\x9co\xa5\xdccF|u\x89\xf0\x94m\x13%\xf9\xd5\xfc\x86\xe0\xf8\xe0\xd8\x85\x1a\x9e=\xb8\xcf\x81\x8a\xd5\x99\xf5\xc0\xfb\xb7=ft\xbasMXW\xe0\x8dU\x03\xa7\x87\xb8\x1e\x9a\x8a)\xf6\x0e\xfb\x812\xf0I\x05dW\xd6\xb8e\x1f!<\xc2\xd8\xfc)[\xf3\xf5\xa1\xac\xbf\x1b\xb5&\xd3\x16\xb8*[5n\xe0mW\x1d(#\xac\xa6\xea\xb3\xa4`u\xb5\xcak\x08\xaf\xb3\x02\xa4\xbf=\x9e\x8d`\xff\x80\xd9q\x98\xa6\'\xf9\x94\xed(\xc8\'\xad\xb9e\x01\xd9\xf2X\x99b\xbbp\xec\\\xb5\xadk#\x88~\xfe\x80 \xd8\x17|\x1buI\xc9\xb6\xae\xaeLS\x9d\x9f\x12\t\x82\xa9\xaf\xcfx\x87\t\xc9\xdb\xa43J\x9cD\xbed\x8c\x18\x8f\x1c\x15\x1a.\xfd\xc9*Z\x9b\x16\x95\xc9\x03ip\xbd\x87*\xa2I\xf4\xa3N\x9e\x1e\xd0\xf1w\x88\xe9#\x10\xe0\x86\xb1OQ \xe1\xd0Mj^\xf0\x89\xe5\xb5\x08\xd2\xabk\x84i\x1eA\xabg\x17_\x881\xfb:\x14\xc5\xfd[n\xden\xbdx\xca\xd7\xfb\x01\x82\xaf\xe6\'\xe6\x90v\xc3\x9eSq\xc9\x7ft\x80\x03X\xfa#3\n\x95+\xef\x9c+l\x1c\xe5\x9f\xcc\xe7\xdd\x85\xf5\xf5^:V\x81}\xb6(\x952\x0e)\x91\x94\xb8\x02js\x05y\x88\xc7m\x85_\x11*\x1b\xb5\xf4\xf2\xc36tWB\xe6\xc0p.H\xf4\x94\xdb\xd1\xe1m\xec9\xa3o\xd5I\xd8\x8d\x8f\xb6\xa0\x0e\xaf\x00\xa0b3= \xc9,\xa0\xa8b\x97`\x0e.<\xf2T\x9f\x1d7>\xc9y9v\xae^x\xca\xdd\xcaA\xf1K\xea\xb5)\xd7\xc5\x1d\xcd\xd4\xb6\xf7\x90V\x9a\xeaa\xaaX\xa1u\xc1\x17H\x84\xe5?\xf9\x8aPGB\r\xb0\xf29\xbf\x05^y{\xe4\xaf\x93\x08\x8dS\xd8\xd4\x91\xc3/\x1e:\xf8\xb4\xc8J\n\xe7\xf9ZB\xe2\x18\x0c\x1e\xa5G\xc9\x9et^\xed\xc1\x9d\xbc>A.\xa2\xee\x1b\xe70\x03\xeanD\xa2H\xb0\x98\'\x93\x1eA\x8bjOwz/\xf7\xb7l\r&\xa2\x11\xdfB\x88\xb4^<\x0b\xde_\xa3\x99?\x1dV#\x84i\xb2\xf1\xf2\xb6\x13FiT\xb3\xc6\x8e\x93\xc6qU{\xf6\x19\xe3R\xfa`\x0e%\xc7\x98\xe3[X\x04\x8f\xcd\x85\xee\xa7\xc1\x91j\xcb\xa9s\xcd\xd2\xe5\n#m<e\xb8B\xdb\xb7\xff\xab\x0e\x1a\xb9^Y\x82\xd0\xbb\xf2\x0b\xab\x02\xfd\xbf\xa4\x9e\t\xadG)\x1dF\x1a\xd0K\x85\x82E%Y\x13@\x1eB$\xb6\xa4\x95\xc8\x88\xb5\xcf\xd4?\xa8\x10Q7\x85 \xfb\xf1\xcet\xc9\x16\xd1\xbc\x8b\r\x82\x95*p\xa5E!\xab\xee\xa6\x9d\xcb\xeaj\xa5V\x9aUR$\t\xf91\xc2\xee\xc8\x96?\xeb\xd7\x1e\xb4\xe5\x95\xdbD\xdb\xfd"\x9c\xf0\xf1)[<;\xdc\x93\xd5v5\xcep\xc5\x9az\xa9?\xb7\x8e\x7f\x03\x89\xeef\x9eQ;!\x11\xfa\xfa\x82\x160\xd99\xa0D\xfb\'_\xb4\x10s\xc0\x97A\t\xf2\x9a\x02\x878\xf0d\x01N\xd6~\x8dc;\xff\xac,[\xdd\x1f\x1d\xe7s\x804\xf8H\xd5\x9c\x7f\xbam5$\xb9L\x06\xc3\xdc\xcc$\xac\xb0\xb0w-`\xd5\xdb8\xea\x81\xc9\x18\xe3\xf2\xaa\xe9q!0uq\xdc*\x0f\x1fe\x16\xe3\xad%\xba\xbbU\x8e\x13v\x19\xe7ylo\x15\x92\x19\x93C\xd2<\x88\x04\xe5\xdb\x826\x9a\xb7\xdc\x9a\x85Z\x89J\xb4+A\x92\xec\x83\xc4\xa6\x1d\x08\xb9-\xce0\xc3\xac\x0b\xbb\xb3\x1fg\x15\xeb\x07\x03\x13\x05r9\xdf+\xd8\xe5\xb3\xe7\x97\x96\x0e\xa7 nZ\xb0\x8d\x80\x84\x16\x8cB\xe6j"D\x8e\x86"\x0b\xa6\xad\xb1\xb1\xedu,BY\xc5\xb8\xb0\x84#\x9f\xef+yq\'\xd0\xcc\x11\xb9.\xaa\xc0\xb2\x8du\xf6\x9b\xb0\x1a\'\xb0\x89\xa4m\x95\x1e%\x13\x11\x93\x80u\xa81H(\xa9\xb0\xa4\xb4\xde\x04\xebK\x8ab9\x16\xe0c\x81\xff\xf6ni8\xdbr\xbfW\x08\xd1\xe8\x8c\x9d{\xda\xef\xda\x85\x9d!6\x9b\xcb\xa6\xcd\x9b{h-x"\xbc\xd5\xacR8 \xd0\x99\xae\xd8\xfe\xef\x97\x8d/\xeefU~\xf3!\xf0S-\xc2\x8e:\xd7M\xfe\xed?\xea\xe8\x0b\xa56{g|\x0fS.\x9f\xab\xdb\xc9\x83\x16\xa7\xee\xfc\x84\xb7\x91\xf6%\xaa\x1d\xfc\xc41\xb4\x80T\xb0\x8a\xff^f\x83\x8b\x94@\xe3\xc3\x0f\xa7\xad\xa8-W\xa7\xce\x0cQO\xe7k\xd2B\x9aD\xc8\xcd\xb3\x03\xc2Mm\xac\xf2x\xa4\xaa\xc3\xda\x17\xa6\xb7!\x9b\xd2>\xaf\x9a\xe5\x7f\x84\x00\xafi\x19\x07K:\xbbw\xd4\r\xb1\x97\xee\xc7\x85JQ6=q\xf2\xe2IV|\x0c\x120\x1a:}\x0e\x10>\xf9\x82\xbc\xe3`\xd33~\xc3\xfca\x06\xfc\xbf\xb5u\xa6r%\x9faBk=]2QH;\xe6\x96:m\x15z\x84\xc3\xe8\xf9\xa5\x87Y\xf8\x9deVIm\x8c\xa1\xc8-\x0b\x8d\x15\xf1}\x8c{x\xce\x9c\\"\\!v\'\xcddL\x9c\xe2\x1e\xc8!X\x9f(\x0fn\xdf\x10>L\xa6\xab\xda\x15\xc6\xdbx\xc0v<\xf4\xab\x80T\xf4\x157\xd2\x97\x13#e-\x9c\x11\x87\x8b\xb4\xe9\'\x02\xa1U\x0f;Q\xf2Z\xd2/|:\x0b\xa8-#\x06,r\xfe\xea\x18\x8f%\xc5O\xc1\x92\xaflI$\x07\xd3\xba\xf45\xad\xaa\xe5\x18\xcc%/\xba\xef\xaa\xba8\xba\xab\xe1\x83:,\x95\xce\xf2\x8a\xc9N@`\x94+\xe6\xa53\x1dk\xc5\xc7kX7G\x00|\xa5\x1aL\xec\xf0\xe5p\xbaI\xd7\x97\xde\x1b\x15\xd5 \x888\'\xa3\x15i\x8b@\xef5\xe78lq\xa3\xe2j\x0b<\xb2~I[\xf6\xd0Xx\x86Dv\xae5\x81\xaa\xc2\x89r\xff\xa3B\xac\xf9\x07=\xc2I\xea\xbe\x03\x02\xc9f\xffJq\xd7\xbd%\x84\xee\xda\xec\x11\x00\xd5=-}\x98.u\xcd\xcbb`d\xc5\x87.h9\xb5\xdc\xd4nd\xd8\x06I\x9f\x81y\xeb\x07\xfb\xd4\x06Y\x97\xc5\x16\xdf\xd60\xdb\xfc\xa3L\x1cj\x0f\xe2\xc9\xd9;\xcbe\xc2\xfa\x94\xe8\x11\xb1\xc3\x95\xb3\x08\xae\x01s\x9bF\x86\x1e\xa3{\x89\x9b\xf2fx-\x9c\x0f\xe5X\xaaj\x85yP\x16\xe1\xd3Mg\xdd}\xc7\xe3h\xb5\xb0*\x85}\xf8\x15\x9a\x9b=\xed\xe4\x0e\x8do\x89\xca\xb5\xc4\xca\xc8\xd8\xecn\x83\xbf\x066}\xbb\xa98\xd6\x81\xfd]\xdcx\xbf\xceF\xd99\x02G\xcf\xdd\xed|\x18n\xb4\x0c]\xb5;\xb9\xcc\xb8\x9c\x88\xf9j!neq\x7f\xa2m\xf3\x05\x1e\x8dsL\x11kv\xdaO\xf5\xfc8^\x96>\xb0\xc8(:\xd9\xc1\xf5:>\x11\x1b \x1a2,\x9a\xc9~\x8c\xdd\x8a\xcb)\x80?:5\x8e\x85\xa3\xd3\x11g\xban35\xbf\xc3]\xf9\x94^p]\x87\xe3\xfdz\x9fd\x7f.\x80Q\xdc*\x07sP*%\xb2\x99\xaa;_\x1e\xee`\x91\xa5\xe8\xcb\x81\xa7g\x8a\xcd\rdd\xc7\xde]\xee\x05\x82\xe2s@{i\x04b\x92Q\x05nL\x0b;\x89>\xbex\xfc\x9d\xdb\xdc\x9e\xcd\xdahg:\xce\xb6Hm=,j^-~M\xedo\xca\x83w\xc5TK`K\xfa\xf8\x84\x17\xbd\xb2\xaf]#\x8bI\xdf \xbd\xee\x9f\xce\x19/<{\x82\xc4~\x1f\xc4P\x13j\xa3\xd0\x0b=\xb8\xe3y\xd9_\x8b@\xad&MF\xce\x03Z\'\xf7*%C\xd1g\xf1!\x93\x88\xbb\x01\x8e\xb4\xdbZd\xf3\x92\x1fF\x1b\xc6\xe1\x99\xbb\x8ec/g\xd9(\xd8%\xe4"\xce\xaf\x98\xb1\xf0\xa6\xe0\xd8\xcc\xebu\xd8\x8bT\x9e+x\x93\x0fw_\x82\x9d~U\xce\x8c(\x99L|y1\xd0\x0f\x9c\x1d7d=\x91\x17\x894A\xad\x88(\x94@aCi\xb2\xde\x1d\x1d\x97|\xb9l,\x9f\xbd\t\xce\xfd<\x98\x14\xf4X3\x0b\xef(g\xb2\xf8\xa4\x8c\xff\x1aj\xf4\xa0\x865B\xfaQ\xfa\x97\x81\'%\xf45\x19\xf52\x12\xd7\xd6\xd8\xdf2\x94kb\xd4\x8b\x07\xdd&X\xb2\x92e\xbd\xa0\xe6?\xfe_b]B]\x93P\xed\xcf.\x15}#Y\xa1\xe5\x90\xbe\xe7Lb_R?\x04I\x176d\xc68\xa0\xdc+\xcc|\xc0\xa5^\xb1X1f\xf2\x84\xea\xf1\r5Q\x0e\xa8\xae\xd2\x1fB\x04\xae\x04K\xfe\x08\xe6}\x84\x8d!n\x00\x0cPF!Z5\xab\x06\xdbxS\x85\xa8\xa8\x80\xa1\xfdq\xb1\x93\xdaCcn\x8d\xc0>\xe9\x91Ax\x81\x98G-\x0c\xa9\xd74\xa3\xaf\xf9\n`\xe4\xb9\xd9\xca\x02\xe2Vp\xa9E,Q\xbf\xc6\x8c\x0cDY\xd7\x01"\x82\x87\x80Pd\x9b18\xe1\xf0d\xad\xc6x\xa6\xd5\x8ba\xe4\x8b-\x08\x02"\rtlN\xd3]21yu\xf9 \x89\xc7r\x8e&\xc1\x06O\xf7n$\x99\xf0\xab(\xc4\x0f\xd6O\xe6\xfcJ\xc2:\xbc\xac\xa1.H\xa6\xd6\x04\r\x0b\xe3>M\'\x04\xb5\x05\xf6\x1e\x96!Y\xbd:\xe3\x03/,xri\r\xc0u\xe5\x0b\xb8\x0b<\xd9V\xf3C:\xd92\x0fK\xdf\xdd\x11R\x0e\x03u\x85v\xa2}\xd0f\xf4"\xde\xe6\xceC\xadrP\x140c\xf8\xd8\xd0\xd2\x00\xe4NSw\xf9\xd1\x15,\x9c\x1f\xda\xe4\x0cAt\xc8\x8b\x15\xefcV\x010\x10\xaa[\xddd\x81\xf4\xcaSgx\\\xa6\xb7\xb4\x88R5G=\xfd\x03\x0f@>\xbfW!\xee\xa6\xfc\x8d\xbc\xbb\xb7.Q5\x00\xc3\xaf\xfb\xcb\x8f\xf9\xdb[\x0b]lZ\x8fALcx\nvb\xdd\x00\xf75T\xb9\xa4\xfc\xfa\xafm\x10z%\nc[rj\x8d\xb9\xea2C}d\x8ee\xed\x0b\t\xc3T\xa0n\x91\x82\xd9\xa0\x14\xd5A\x10\xben\xfa\x0f\xf4\xce\x009\xde\xdf\x8b\x14,k5?\xef\x184u\x9c\x1b\xea\t\xef\x0c\xec\xb3}QA=\xe0K\n\xf7\x0fW\xc1R4&\x9a\xdc\xef\x1dz\x1c}\x89$\x02\xe0eWV\xc7\xfb\x98]9u.\xf6m\n\x8d3\x17\x89n\xb5\xe8\x14\x86]\xb6\xecM\x03*&Rt\xfe\xd3\tA\xd2\xa3\\+]\xf7W\xe5Z\x0b\x91\xc3$\xf3\x13\xbdf\x90\x9d\xe6\xba\xde\xe6\xc3\xa1\xf0\xdf;(\xc9v\x89\x93\x9e~\xf1\x00\xcd$$\xd5f\x03W\xed\xd6\xb9\x88\xb9\x7f\xd1J\x06\xb4\xe2<\xe9\xdb\xed_\x06\xb0T\x0c3C\xf2`\xa8\xa4${"6Z\xe8\x86\x8d*|\xec\x18\xa7\xc5\xbd\x8d\x19s9!\xdeI\xa7\xf1\x8a\xb2\x13g\xb2\x11\x9c\x13\xb4\x8c~O\x0c\xc0\xbf\xbfD\x07\xadm\xc2wz \xd5\x9f\x80\xe7\x0b\x1e\x86n\x1ef\xae\xfa\xa1\x84aF\x85\xf5@\x05\x97\x9a9\x15j\xf6\xc34vr\xc6\xbc/N\xb7\xa6\xae\x1f\xa0\xe6M\x83\xf5@/-j\x10dZM\x82\xbfnW\xe8\xb7oU\x98F\x1b\x93\xcfzj\xaa\x0fS\n\xdb\t?f\x80\x9e\xf7\xcd`\xf5\xb7\x1d(a.\xfb\xe1\n\xe7\xfcu{l\xc7\xc9\x08Y\x1f\x15\xfb\x82\x83\xa8\xc9\n\xf7;\x0f\xdb\xb0\x02\xda\xde\t\xd0\xeb\xa9K\x85(\x03\x86B!\xcd\xc2\x9e\xe9\x92\x9b\xb1\xca\xdd7b\x17\x13#\x9bz\xd7\xe8|\xd9\x0c\xd2\x14\x8d5\xf1\xef\x95;c\x7f\xfe.\xb2\xc5\xdc0\xbb\x18\xaa\xaa\xc6jG^\xd5\x92\xd4\xf5\xbc\x84\x0ftAp}\xcd\x16\xf4\x1a\xc6\xc0\x15\xb4\xd5\xcf`\x01\x05\xdc\x1d\xdd\xd8\xf6\x81\x8b\x15\xf5\xe1\xe3\xae\x17\xd1A\xda$\xc5\x9a\xd0\x03\xec\n\xb7\xd0\x1f\x82x\x7f\x87\x83\xa6\x06\xd0\xd9\x1a#>_nB\xc7\xa5\xddN\xc6\x1b?\xda\xda@\x1d\xbc\x1aM\xba\xa5\x1fB\xc0\x03\xc3x\x8fC\xe0]\xc4\x06\x0cE}9\xee\xa1\xf0\xf6\x91\xc0HH{{(0\x88\xd4mZ\xf7B\x91\x19\x8c~\xd9\x18\xf7\xdf\xab\x1e\x89$\xc9\xc8\xe9\xb2\xbaG:\xb1s\xa8U\xb5\xa8\xf3\xf7\xf7d\xe8\xb5\x97w5R4\x00\x85,\xd39-\x07\xfb\xcai\xdb\xce\xdb\xd4\xfd\x10\xca\x8d\xe6/\x03\rL\x85\x047\x10\xbeZ\xd6\x18O\x87lJ\xe2\xf7\xd4X\xcc\xd6z\x18w\x8c\x05\x97"\xca\x18\xf5$\xf4\x04\xda4\x90U\x99\xfe\x04\xbfO\x95\x8e\x8d\xac\xe3\x8c\n\xaa\xd4z\x14\x0c\x14i"\xea\x81#\xc5\x03?\xc3\xa5\x94\x19q\x16\xace1\xf1\x18\xc3?\xd8&\xe7\x82\xb2*\x06\xc3\x85,J#n\x9a\xe8\xc5\xb8>\x18\x8e(\xdc\xec\xa0em*\x0ei\x92\xb0\xc6JPE\xcc\xb1)\xc2\x86\x93P,\xad\xbd\xd5\xe12\xa5M\x0f#0\x0e|\x0e\xe1:\xd6\xf1\x13\x93 \xd64\xe6m\xbd\x88\xd2\xf1>\x07\xf4-\xc57!^)\xed\x05[\xeaa\x97x\x1a>\xf4\xe5\x19\xcfH\x9b$g\x15\x07\x9b\x98\xde\xa4:c\x8c\xaf*)I\x03r\xc1\xf5 \xdf\x88\x98k\xcc\xb8\x94S\x9fu9\xe0\x7fU>\xccc/0\xae}1\xfa\x94yy\x9d\xb8\xa63\x8cIm\xef\xd0\xe7\xa0\xe7\\\x987r\x8a\x96\xc8H6\x14\x15\x0c\x06\x99>Z,\xb7\xdd\xa0\t\xa9\xc4&\xb1\xda\x16y1\x91\xdb\xc6\xa1\xd9\x06\xfc\xa2\xec\'\xa2}\x0cS\x00\xa8\x86\x06\x14?,\xf5\x0f?CH\xc2,\x83\xef\x8a\x06eVL\x9b_|\xdbh$\xc2\xe4\xa0\x1d\x84\x17\xe2\xda\xbb\x9bY\xd0\xc9z\x91\xa76\xbb\x08\xb3\x17C\xd5\xd2\x01\xca\xf7\x8e\xc5\xa3%\xd4\xc8u\xbfW!\x06\x80\xda\xbc\x1b3T{\xa8\x85G@\x04\xe1f\xfb%\xb1w\x84\xd1\xf1\xc9x\xfa\xdb\x01`\x89\xd2w/\xf0\x96\xb1\xd5\x0e\x14x1\xd4\x06\xa4\x01\xe5\xe6\xa5\x04.\xf5\x05e>\xde\x98\xf0\x10\xff\xd2g^\x8e\xc1\xb5n_\xbc\xa4\x8e\xd6\xe7I\x0b\xf9@\xb5\xad,\xaf\x86\xfbW8\x13\xb4\x82\xde\xd5/\xdb\xdbD\xafH\x87\x12\xb1\x7f\xb3\xe5x\x07\xf1\xcd\xe3\xabh\x04U]\xb8?j1\x8d\xba\x81\xdbD\xa8\xce^\\\x86\xf2K\x1d\x82\xa6\xbc\xa5\x83,!\x8e+\x7f\x12\xe9\xb3\x92(31\x8d\xe6\xd3f|\x08t(\xb6(\x99\xfe\xc9\xcd\xe2\xcc\xa6\x02Vd\xae\x82\xe8\x9c\xa6\xc0y\xbc\x0e\x12\xd3\x9e\x94\xe7e/\xb2\xf1"c\x84y\xd8\xa1\x05\xeb\xabmR\xc9\xac\x07.\xd8\x12\xd9\xe2C\xba\tl\xa0\x0cY\xc4 \xda\xa4K\xdb\xf6\x9ax\xc1\xf9\x8c\x0b\x03 \xe7x\xf3\x05i\xd1w\'\xaa\x89~\x1b\xb1\x159p\xb7\x1e\x00\xa2\x05\xb7\xdd\xb5+L\x03\xf9\xde\x1f\x1e\x98\x81x;Z4\xac\x1e3M?\xcb\xa0\xb9h\xe0\x03\xfd\xd2\x1b\xf0P\xdf\xbe\xd5\r\xc9 \x14C&\\\xd8\xb3\xd8\xdc\xa9\xd6\x15\x19\xb2\xb6\x95\x17\x92]\xa4\xc0\x91T\xe0\xdb\xd1\xf0\x9c\xa6\x17\xd9g\xc0\xd9s\x1c\xf7\x11\x83\xc2\xbe\xf9\xda\x11.B\x8d\x96\xad\xd1\xe7\x91Qd:d@\x9e\xd8j\xf3oo\xe3VA.x\x1b\xe9\xd9\xc6\x14l\xf5\xc9\xa4\xe7\xb6%;\xe7@\x08&B+\x18\x0c\x1e\x1a\xd9ec\x93\xa4\x98\x19cv{\xe6\x08\x10\x1e\xaa\x03*\xdeQ,\xd9n5Yb\xdf\x04|Px\x85c\nN\xfai\\\xee\xc8K%@v\x14\x94\xf4\xce|\xf9\x195\xc3i\xe6\xde\x9a\xfef\xdd\xdb\x13\x1c\x19\xc6~\xb6\xf7\xf3B\xaf\x11@\xb1\xbd\xc4\xb8bc\xaeI\xf93\x8a*\x93\xe1SiW\xda\x98\xb0\xaa;J#\xcb\tW\xaa\x1fQ/w\xaf\xf1\x10\xbc\xadG\xe3&SV\xd9>\xb4\x15c[\xefMF\xb9\xe7\xce\x1e\xae\xcc\x85\x04\r\x92\x8b\xf7\xd2\x1f\xbb\xf5\xda\xb4\xb9\xca)\x94[q$\xdd0m\xd3\xb8+\xa8Y[\x14\xe5N\x84\x11\xb2\x8f)\xaf\x1e\xaa\xae\xb8\x01\x14\x9dNF\xcbn\xdc\xd7\x0f\x83zt\xa1\xb9\xf4A4\x7f\xb3b\xb4\x1eBp\xfb\xd9\xcc{gN\x9e}|\xb3\xdc\xdc\xda\xda-\x7f\x9aa\xd5Yv\xdc\'\xd3U\x19\xe1\xe6g\xb6\x08\xfct`hO\x80E\' \x9d5\xb4\xca\xfd\xa1!\xe0\xf8#C\x08\x11\xb4\xe5\x98\x10\xa6\x9e\xb7\xb6\xcb\xcc\xef\x80\xc7\xce\xde\xbd\xdeQ\x9f\x04\xf6\xf5f\x17A\xe9\xda\xb2qYtJ\xac\x95\xac\xe6\xd6#\xb5=\x94\xd5\x17R\xbd\xaf\x18\xb8\xe5\xaar\xd70\xaa/Z\xd8\x10zc\xb1\x1d<>M\xdb\'\xc7CR\xf2\xd1\x0bhF\xba\x91J\x81,j\x94}R\x0c83tO\x135Y\xddO:8\xda\xf6\xdd\x97\xbf\x986\x8c\xc0\x8aG+\xa3\x02\x12\xfa\xc6yq>\x02\xdf(\xbeITYk\x9d\x18\xa2\x89.K+\x87\x88\xc9`z7\x01a\x94\xe2\x1f$\xcbT;\xdcpI\xbb\x17\xdb1{\xcbK\x99\xea\xc5\xc5\xe1\xb9"\xf5\xe0@\x14\xa6\x8a\x1e\x85\x95\xe4\x89\xddec,\x80\xef(Q\xd4\xaf\x8fC`\xafX\xb5\x0eph)\xf9\xf0\xdc\x10aO`&\x92Li\xca\xdc\xe0\\\xb1\xf2\x8al\xb8p\xa9\xed\x99~;\xe6\xcf\x1a\xeef\xe2\xe3\xf9\x03\xe1\x07\x84O\xcf\xdbB.\x1dvP\xc5\x8c\x06s,\xc7+\xe9w\x9e\x9b1I\x08G\xb4\'\x95_\x0ct\xbfK\x9f\xf5\xa0\x8d>\xcc\x9apy\x9c{\xda\x92\xc1\xf7Q\x1d\xc6\\r\x9f\x10\x06\x1a\x8f\xce\xc4Ni\xbcdXC\xe7p\x16\nP\x07\xc2\x11\xf0\xe3A\xdckN\x85\x96\xebc!O\xcb\x8c\x0f\x07\x00\x89,RUB qmkp1\xed\x8b>\xd38\n<_\x13\x06\xa1\xf0\x97\xbbb\xf9\x8d\x82qv\x8d\xca\xe0\xa8\xbfbtwJY\xe6\xbd\xc9\x8c\x8f\x8cL\x98\xe5\x12\xc8X\xa85\x94_\x05\x95uO((lz\x00\x9f}5\xfcb\xe15\x9ah\x8bZ\x07\x8a\xd5\xd4\xfc\x13\x03r\xa4\xd6\x11\xdc\xae\x1d\x0f\x8aCB\x1a]\xc8\x93\x04A\xc9Z_\xc3\xb8\xacu\x1akl]d\x11w\xf3\xd7t\xa2M\x900\xd8y\xcd\xda\xc8\xb3i<\x82\x16H\xb4} :o\x8a\x97\x1a\x8c\xca8@\x82\xb1\x8c.\xb8~L\xb2}\xbc\xe3\x02\x03G\x10"\x9c\xc2D\x00\xedy\xf5J\x1fDj\x13S\xc8\xe0)\x83\xa1w\x1b\x0c^\x9fa\xed\xec\x8e;J\xee;\x95\xfd\xceo/tE"\xaf\x95\ne\xd6\xa1KZ\x7fJ\x15\x9e\x1f\x9a \xa5X\x81;$\xa6\xf7\x9b\xd8s\xd5\xc7\xba\xf7b{@h#\x7f[\x13\xba\x19\x9eW\xf5V\xe63\xd5o>o\x7f\xaa\rhG7\x0e\xa50v+\x8dG\xea\xad\x90\xe6W\xce\xc9\xbc\xdep\\\x1f\xabf\x99\xee\x06n\xac\xc5\xc5\xf3na\x8ap\xdb\x97\x99zG\xe3\x88\xd9U\xf1\x8f\x10\x81\x1a\xf36\x82\xccp\x04\x19\xe29\x88\x01\x1d\x07\xa1\xf07\xe7>\xbaOB\xd1\x81\xaf\xca\x00O\x80\xbe\x10\x8d\xb2]\x08u\r\xa4\xd6==\x0b\x91eR\x17\\Y\xd4\x1f\xbf\xee\x08\xe9}\xc0>\xa0\xd3\x9d\x85kED\x90-`s/\xbc^\xa0\xa6xZ\xcd\xa7$BgV\xd4\xe7\x0f\xdf\xbf\xee\x01s\xa5\xf0uU"\xcdu\x16\x03\xb2\x04O\xfb\x94\xaf\x08C\xc6\xba+\x06,^\r$J\xd7\xe9\xf8\x0e\xf4\xabb\x13\xda\xb3\xf5\xb92\xefV\xb0\x9b\xd9B^\x80>\xe7\xd1B\x87\xc3\xc2\xae\xe4\xc5\xf9\\*US\xbb\x03\xe3!T\x9a\xf7s\xdc\xec\xe2[\xa9\xdb@\xcf\xd0\x8a\xbd\xf8\xc8J\xc4Q/\xb0\x00(_\x1f\xf1Z(\x10\xbc\x91\xec\x95\xc0\xca8Erj>\x06\xb7<\x89Ei\x1fP\xd9s\xc4>6\x10\x01\xd4\x8aduK\x19\x80\xea\x1b>\xbc\xb0\xcc\xf6\x1d1\\W\xba\x0f6\xec\xb3A\x8276\x88\xd2\xaa*s\x1ao\xf0S\x7f\xd4kzo\x1f4\xfapQ\x16\x13\x00\xab6\x18\xd7\xcb\xf2qW\x88\x9b\'x\xe0\xf4\xf6&\xb2\xc6\x8b\xa8\xdf\xa2#\x10\x14s-\x96\xfa\x0fF\x9d\xc0\xb2\xd2\x07\x07;\xd77\'yY\x86Z9L\xd5k\xd0\x8c\x8f\xce$\x12\xec\xc8\xd3/\xb5\xf661\x1f\xd3X\xe1\r\xc1\x8d\x94I-\xb5aU\x9a\x8b\x82\xc7u\xad\x8b\xf8\x86\xd5\x1dbu\xbc\xcef\x14d1\xf7?\xb5\xb3c\x8f1\xe0\xa1\xaf\xf0\xa6j8O&>#\xc6\x08\x9f\xf67\x19\xf6\xcf\xea\x82[\x92\xe1\xa4\x8a\x01\xb3\xa0>\xdd\xae/DV\xa3h\x9c\xff(\xc0{\x00omP\xbd\x18\xdb\x86\x9c\x9b{\xbd\xeb\xca\xc5l\x86P\'\xf5\xbc\xc1\xe8\x15b\xe5lJ\x8c\x15p2\xa1\xcb\xceq\xba\x03#\xfc\x83\xf3hC\xce\xda\xf8\x11[\x03\x98\xff%\xc2\xce\xbf\xe2\xf9\xa9\xa0\xc8\xed\x1a\xcd\x93\xe1\xbc0T\x1eD\xc2\'\xc1o"f%\t\xf8i;\xd07\x01q\xea\xa2TR\x1e\x8bQ\xc2r\x86)QkNf\xc7\xf9e9\xe7\x8c\x8b\x9d\xb6\xe7\x0b\xf6\x86\xfa$js\xfc_\xc0J\x02/U|c\x06(\xb8H\xcf?O\x9f\x87\xc0\xffxa\xfc_\xe2\x1d\'i\x99\x88V\xef\xee\x92\x80S\xe4\xb4\xbeF\x81\xf4\x03+mg"=\x162TS\xd5^\xef\x9f~\x06\x99\x9d\x80@h`*w\xa2\xed\x84*\xcfpF{\x07\xaf\xca\xa4\x18k\xd1Y\xd2\x17\xbc\x07\x8e\x1c\x1b\xf7A\x0b\xc6\xbe\xa8\x03\x7f\xea\xd2\xe0\x13\x8c\xe0\xf2\x98\xa6\x1fJ\x01\x07+/b\xde-\x049\x9c\x83\xa5\xaa\xb6\x8dk]- \xc7\x1a\x91\xa6V\x1a\xc6\r\x08\x16\xb7\xb1\xda{\xe3}\xa6z\xe6`Y\x88\t\xe7\xebK\xb9\r\xf1\xb3\xd10\x10\rR\x1f$y%\xa6\x85\x8bw|&U\x95\xfa\xb8\x1d\xdb\xb2;\xee\xee\xa6\xd6\xab\x0bK\x9a\xed\x8b\xe6z\x97"\x15\xe0p-6\xd6K\xaa|\x00#o*\x076\x9d\r\xc2_*pcM2\xe8\xfd9\xaaY\xb0{d^\xaf\xb2]\x8d\x03#cQ\x04\x19\x8amo\x08\xe7e\xe0E\x11\xf9,\xe8\xb5k\xaa\x07\xe9\x82\xf4tw\x83<<\x92\xe4[\xbb\xd7\xb55\x19\xb7\xed\xe9\x7fd\xf0\xbe\x112\xc5\x186\xf0L%\xaa\x9d\x17\xe8\x94\xdd\xf1\x83\xd7\x89\x8e_\x07\x03\xa7\\\x1bz\xa71\x96\x84m\xda_[\xa1\x91o\x13\x0b\xca\xf3\x8e\xf2\x96J\xf3\x11k\x0b\xae\x86|\xb6[\xd40\xc6\x907\xf5\x92\x1bK3\xfejR^1"\xb5\xeb\x87\xf7\x06\xb3\xd0\xac\xdf\x8dq]\x84\xf0\xb7\x05\xf2,r\\\xa5]<\xc4\x95u_\x9c\xb8\x1b\xe3\x05\\\xbd\x18\xb5\xbe\xbc\xd4\xc3\x03#\x95R\x11\xa0\xe4[\x10@\xff\x9b\xa2\xb9{\xbe\x802\xbc\x84y\xa4h\xdduEs\xdcC\x0cV5\xd0\x97;\xd1\xcd:\x95~\xa3\x1fi\x86\x0f\x8aaP#*\xa5(mhS\x1d\x7f\x1e\x02`b.|\xef&\xeb\x84?<St\xf8\xc5f\x92_@$N\x86h;X\xf6N\xe1?\xd2W]t\x940\xd5\x88T\x92\xd1\x8b^/9\x97\xae \x00(I\xde\x0fY\xbe2\xc3\xe7\xce\xc3WR\x97\x8a8LC\x16c\xb3R\xd9{\x87s\x91J\xd1,\x1d\x05\x13\x85\xd5\x16\xd2*\x16\x87\x92R>&\x9c9\x01\xbc<9\x02\x19\x0eS\x1ce\x14\x10\xfe\x1c\xa9l!&\x04\x0bc<|5I\xc2\xce\xe3\x14>f\x8c\xe0a\x10\'\xa7\x91r\xe6J\x9d\x7f=\x14AjQ\xb6\x9d\x05\xa7#\x93\xed&\x1c\xcd\x123\xa2\x18;\xe8\xdess\xa5\x1c\x80\xb5\xadr\x95F\xdb\x85@%\xe5\xf9\xec@V\xcdM\xd6\xbf5\xfc\x90\xc9\xb3\x90\x99\x00\x1b\xec\xd3\xc4\xb71\xd0\x00\tb\x18\xbe\x17=\x1f<\xd0\xbd\xcc7\xb8_C\xb4XU\x01\x83\x1d\x08\x88\x17\xb0c\xa8\xb9\xb3\xf9O\xd1K\xddc\xda\xb2Q>\x1cU\xe9\xca(\x1aMN\xd2\xcd(\x81\xf6\x1a\xc5\xef\x0f\xcf\x04\x1f\xfbW/a\x85\xb7\xbb\xe6\x83\xeb\xb2N&\xaayh\x07\x14@C\xc1\x8b\xee\x047\x8fj\x13\xbf\x15\x8e\xa6\xd7B\xf2\xc4\r\xf1\xd9)\xd6\xa77\xcad\x81MC\xcaPM\x93b\xab7,\xe7V\xa4\xbc\x132\x9d\xd8\xc5\x16\x04\xbaD.#\xc3\x9d;,| \xa3,\x92\x99QT\x994t\xb5\xbb\xd3L\xaa\xb9\x00\xb22\xaeV\xeb^a.&O\xc0y\xab>\xc9\xa8\xfc\xa8\xb6\xd6\xd3V\xa8\xb6\x8er\xe1]\xde\x8eo\xd8@\xdd\xe2\xf9\xe5R\x88k_S\xc7\x08\x1e\x80\xd0\t\x11\xba\xa3]QP\x83\xceQ\x06\x1e{1\xa4\x0fM\xd8\xd3\\[\xb27\x82\xdd9*B\xb6b!\xd9\xe1\xee3\xca\xd0\xfe\x94\xa5`m\xb5\x19\xb0\x90\x17\xa77\xf4\xa98\xdc\xd0\xd7f\xd3o(\xd8#D\xcf\xa9\xed\x97\xb5\xfd\x88\xb17\xaa\x17SQX\x9eY<\x1fa\x8eO\xeb\x17\x99\x02\xe29\xdf\xb6\xd9\x7f\x1d$\x1c}J\xe0>\x83\xcdD\x14\x05p\xea\xf8N\xe3>\xf5R\xd3x\x86\xf6N0\xd5\xb7\r\xea7\xef\x05Q\xb1=\xc5\xc5\x01\rjA\x80kT\'\xe3B\xd7/uj\x87\xa1\x1cC\x17k:E\xed\xd5\x14\xd1\xc5\x89\x998\xeb\x80\tfTjox\x10A\x81\x0f\xc1=\xa8\xf4$\x86Y\r\x88\x96\xd0\xe5y\xe4s\xa9\x1a\xf1+\xe7\x87\xc6\xf5\xa2\xce8\xb3_\r\xe18\x87\xe3\xf00(\xa3w5y[\x19\xf6\x940\x95?M!\t\xfd\xd9\xc6&\xd8\x1dl"\xabf\x89\xd6A\x16$`\xed\x97\xaa\x16\x98\x9bT+\xb4\xb3)q\x12\xda?\x03\xdc\x83\xd8\x91\xba\xf0\xed5\x89\x8e!\x8c\xc9\xed\xe7\xc5\x00\x0f\xf2-\x8ef\x88\x0f6\xcb\xe6\xf1\xf3\xae\x85*\xc6\xe4<\t=\xb2\x8a\xafP3\x89\xed\xadM\x11\xb3\xdc\xe5r\x1f\xbd\x90\xc2\xd0\xb9O\x8b\x83\xd5-\x14\x8cm\xdd\x1a<\xc0\xf4\x85_\x9e\xab\xfa\x87\xb2N\x7f\xd8E\xc0\x98\xff9b\xbbn\xb5\x07F\x80\x05\xd3\xc5\x15\x86\xc6\x12\x17\x86\xc0(C\x85\xaa\x87i9\xdd5\xe4\x06[z\'\x8di\xa7n\x08)L\x9a\xa5r\xfb\x1de\x8a\\\x1b\x8b\x97Q\x91\xa6\x826Uz \xe5S>\xe3\xd3\xdd\x8e\xa6\xa3IU\xbfZ\x9eL%\xe4\xb4\x1a\x87\x942\x94\x9fp\xd4\xf0\x17\xe9\x118Q\xca\x1cva\xca\xbc\xc52\xb5\xdbk^U\x12^P\xa0\xe0DS=\xa0kR\xbe\xb5\xd3\xec\x13<D\xf3\x07\xf8-\xfa\x82\xdb\xb9\xe2>\x0f!E\xaf5\xc1\xfe5U\xf8\xcfj:\x88\x8dS\x93\x9b\xe9\xd6\x8e\xd6i\xa3\x97*o\x8a\xd2.\x0b\xf4\xfb\x86u\x9d\x08\x86\xe9\xb8\xbb_\xee\xa5RQ\xddQ\xed\xc4\x00\x93X\x88\x94X\xbe\xbf\x05\xa3L\xac(M\xa97\xce7\xe8*\xa2\xd2\xbc\xdd\xa4p\x8f)\xda\xe8\x04\xaa9\xc4f\\\x8a\xe88\x1b\xe6\xaf\xf4w\xb2t\xfb\x07\xd7\xda\x17\xb6\xfa\x01O\xc9l\x8a\xbb\x13\x11\xcf,\xf3\xf7\x84u4R\xe4X\xa0\xc7\xed\xefO\xe3\xed\xbf\xa2\xa9\xf2{\x02\xb0\x89~\x9bd\xfd\xdb\t\xeb\x9e\x0c\x12M\xb6\xd9\x8c6%\x1e\xf0\xb1"\xf9R\xa5\xf4\x93\xc9\x92\x91G\xdb\xd71 W\xcb\xfeTJ\x85\xdb_u\x87\x16Y\xf74\x1f\x11Ur6\x80\xa8\xe4oSG\xdc\xd7\x100\xcf\x11@\xb8\xba\xe8\x89\xd68a\x1c\x86I\x0e\x12#\x9c\t\xa2\xc2S*J\xce7\xfc\x85\xfa3\xcb\xb2Y\x8b\xfb\x89\xa5\xa6#\x9e\xb9\x83\xa2f\xa1q.\x16\xe7<\x92\xec:\xab\xc6G\x17\xae\x0f9\xab\xbc\xce\x97\xbf\x1f\xb9:\x94w\xe3\x9f\xe4";\xc7O\xa6\x02\x02\xd8\xc9\xc7\x9a\xca\x85\x9c\xea\x89\x0f)bD\xeb\xf7\x15\xd5h \x92\x00V\x05\\\\\xf3\n\x8e\xdbd\x9c\x08\xcb@%\x96-\xe2\xe1<\xc6~r\xb7\xf2\xd5\x1dH\x89\xc4\xcb\xcc\xa9\xa3\x98\xf4\xa6\xe0\xfc\xe1\xc7\xc5n\xf7\x1f\xba}\x17\t\xff\x07\\Iu\xb9z5u:\x18\x9c\xfc\xf6\x88\n\xb6?H\xb0\xf4\x94\xfa\x8dq\xcc9\x1d\xfcl7\xdc\xc0Bp|*\x14;R\xb1#\xc63\x03\xab\x81\x99\x9d\x82\x1f\xbd+u\xaf\xf9"\xd29\x84\xbc\xc1z\x07\xa0\x19\x05(\xc15\xb7\xe1\xe9\xda4\x03!\xdb\x1b\xfd\x87\xcd\x98\x91\xd7\xf0#>\xe6\xae\xfbe\x14\xec\xcd\x08\xc4\x87\xe6\xf8\xa5u\x05\xaa7*\xd5\xa77\xbe\x06\x80\x82\xe7v\x17\x8bG\xc7\xdd\xed\x88j>\x1fe\x14^\xffw\x15\xad6s\xb6\xec\x97\xc8\xe9\xe5m5+\xbd\x92\xb7\xa7\xcbe\xe4yt\x98F_\x10\x88\xf7_\x1f\xd3\xc0_D\xf4\xf8\x1b:z\xda\xe07;\xf5\x16\xc0?\xcc1P\x98\xfc\x0f\xe4\xbd\xb1T\xeaF\xab\xcd\x04&22\x14\xe8\x97\xd9\xb8\n\xe3\xf7\x00\xe7}\xc4\x89*\r\xd1M\x9e\xfb0\x92R\xa3\xc0<\xa3sB\xbb\xf7\x04\xf4h\x9d\x1b#\xa7T\x00;ulO\xc4P+\x8cJ|\xb4\x0fQ%\x07c\x8eDB\x92\xae/\xff\xb2\xc0\xb3\x92\xf1\xf3\x85\x87V\xaa\xcb\x1c\xcd\x13.#c\xde\xa4\x08+\xd5-\xa8\xa4\xf2\x06\xa7\xabTl-c\x05\x84\xf2\x0e\xa1\xa2\xafpQH\x015\x86A;\xa9\xd1\x93\xcf\xaaOJL\xbeez\xbb\xb2E\xcc\x14\x0e\xe0\xdd\x11\x0eJ\xd0X\x10G\xa0\x05\x96Y^$i\xcc\x7fi\xc4\xf8\x82\xa0\x99\n\xa5$W\x94\xea\xbdA\x06\xc0RL\xb6z\xe8\x1e\x8c\x99J\\\x00t\xf6\xdc\x8d\xd4\xeb\x9aa\xaf\xa4s7\xb9\x0e\xa9\x1b\x9e\x99 \xc1s\xed\x9d\x03\x1dj\x0e\x83\xd1\xe3\xe6\x81"\xb1+\x7f\xc1\xf9\xb8\x19\xf4\xcc\xc2\xe4\x15T\x8aM@\x87\x1ais\xb4n\x9b\xdc\x9f\x01"sN\xb4\xff\x17\xf4\t\x93mm\x1f"\xcaGKP\xa9B\x08\x17D=\x17\x0eTqv\xcc\x92S\x11YP\xcfN\xd4.\xac\xc0 \x8a\xaa&%\xde\x1e\x8b\x8e\xf2\x8e\xebw\xd9m1p\xbd\x89\xee\xf4\x8d\\\xc3\xc7\xd0\xa4:q}\x86\x8d8W-\xf3\xc0\x1b\xbd\xaf7\xb6C\xd0\x97\xa1`\x82\x16\xc4\x1d4.\xb1\xf1l1H%;\xcf\xc2\xe6\xa6H\x01\xf5c\x9b\xa7\xa0\x10\xa2\xa3\xb3\xc9I\xf5\x805F\xf3L\xa2\xa6e\x9e+\xc7XO\xbc\xc7\xf2\xad\xc9\xa3Wp\xb5\x0f\xaa\xf5\xa8)x\xb6\x0cPzz\xfb\x8a\x91\x98(\x8f\xda\xbd_Y\x17W\xb5\xf5\x96\x06\x92m&\xf1\xc3\xd6\xab~\xddv\xcd9\xdf\xb1\xbb\x9dM\x83\xe8\x8e\xa5\\C\xd7\xb1\xabMBi\x895dm\xc6\xebY\x8f\xbfi\x03\x94\\\xa7!W\x1e\xbd$t?\x83\xbe"i\xc7y\xc0\xe0i\x0eu\xb9\xe5\xc4_\x9bz\xaa\xc9\xe8\xca\xbbi\xfc8&\xe9\x96\xfc\xec\x1emb\xb0I\x9aCi{\xef@\xf0-\xc4%\xbb%\x1d\x05\x057,\xb5\x1cI\\~#\xfb<l^}\xd5*\x89\xa0\xd34\x8f\x96\xb1\x11\x87\xc1\x9e\xc2c\xdc\xdcx\r.\xfd\xfc%:\x86\xd2\xb6\x1eG\x9d\x12\x1f\xaf\xdb<X\x95c\'\xfe\x07\xe4\x8eT\xfd\xd4\x1fN\x00\xb9[\x19\x87\x0e\x8apq\x00\x01\x8c;\x9f\xe1\x04\x00\x88\x07\xb9U\xb1\xc4g\xfb\x02\x00\x00\x00\x00\x04YZ'
    compressed_df_intp_routes = b'\xfd7zXZ\x00\x00\x04\xe6\xd6\xb4F\x02\x00!\x01\x16\x00\x00\x00t/\xe5\xa3\xe0\x06\xe0\x02\xfa]\x00@\x01N{W5\xf4i\xa5\x1d|\xf2\x9b{\n\x9f|c\xd7\'q|\xc9g%\x14\x132%\x94\x13\\\xe0`"\x04+\x84m_\xfb\xf8v\xe6\xde\xeb)V\xd1Y\xcai\x93j\x97\x002L\x15b\xc7s\xe8\x12p(\xdbm\xd8Fe\x05\'\x8d\x07\x18\x01 \n2\xc4\xb5\xa4\xba\xef\x9e\x01\xa2\xa2m\xadN\x1d#\x87\xed\x1f\xf1o\xbeKk\xf9\r\xcf\x89\xe5O\xe8\xf3\xc2\xd6\x0e\xf6\x81w\x1el\xcd\xd6\xfb\x18\x1cSb\x9e\xefq\xf3\xc9\x87(U\x9c\xbf_H0\xc0ZC\xae\xc4\xf1SJ\xa4\xf8@\xed\x14\xc8\x19>\x1b\xb4y\'9A\x16\xb4\xf2o\xe5\th\x08)\x0c\xd77\xc0fy\xd7\xa0\xa9^*\'6\x13\xf2\n}\xf3\xc6cl!/\xb2-\xaf9\xdf[\x07\xdck\xd4d\x0c[\x9ciV\xd1\xb5\xa9\x14"\x114\xc6E>y\xdd\x05\x112\x98e\xe4\x90\xe5\xd0<\xcc\xac\x01\x16\xbek\xdb\x00\xc7\xbdm\xe7\xb7\xec\xbb1\x1fA\x15^4\xeaLi\x9a\x1e/\x9dB\x99#6Z\xc4b\xa4\x7f>\xb0\x13(L\xed\x0c\xa5&\x83\xd7\xeev\xfb\xa42?V\x13\xfd\xb7\xa4RQ\xdfG4\xd2\n\xa6\xfb\x97~\xb3\xed\x1d\x8bTfFFlL4~\x06\xa1\xd0\xa1(\x1f.\x1a\xc4\x8cH\xf0\xfd\xc0\xe5\xf4_BaC\x9a\xc2iHR\x9d+\x9a\xea\x1a\xf9\xab\xc7\xe8\xb5\x1e\x0e1M\x8b"\xce\xb9\xb3I\x972\xbe+\xec\xf1J\xc8\xef\xd1\xa1-\xa2\x1fV\xd8\x90\xf7{\xb6%\xa8\x81\xeaQZ\xea]T\x98 \xa4[\x1e\xb8\xca\x91s\x13i\x95Sto\x8b\xba\xa7\x91{H\xee>F\xcf\xa1\x03\xe5\xa8\xfb\x94\xa8\n\x05\xccO1\\\xcdH1\xb4\x87\xb9\xec\xea_\n;v\xbc Go\xc8~\xf7\x88\x16\x03]\xa7\xcdrx}[\xdc\xec\xa761\xba\xfb>\x8932\x94I\xc3\x97\xd0\t\xe8Z\xb1vo\xfe\xb9\xfc\x9b\xbeA\xde\xe8\xbb\x93\xc4\xb7\xb4\xb4\xa95\xbdET!4\xe0\x91S\xda8\xb3\x9b\xee!5\xf6c\x9e\x99\t\xd2pu\xe9\xfa\xda:,\xd0\xd06\x0c\xb6\xf5\x9a\xd2\xd4]\xea\xceW\x97(Z\x02\xa1\xad\xc0\xd6\x92\x8e\xb9\x1e\xd5Z+\xff\x95\x8f\x80\xd1.\x05\xef\x059\x9bD\x0e\x935\xd2\xb9\xf3\x0b\x16K)\xfdz\x8bT\xde\x91\xf9\xfe#@)7\x9b\x94\xbe1\xa5.G|\xf2d\x83\xd3\x19\xb9c\xc4\xbb\xda\xd1:Wy\x8c\xb8P\xc7\x97\xdb\xee\x15\xde\xb8\x9ckq\xc9\x7f\xc0\xeb\xe2\xa4Z\'\xeb{a\xcc4$\xf5T`\xaa\x89FB\xb4\x91\xde\x19\xf6q-\x0e\xf5\x80J\xf4\xd8\x91\x9a\x0e^p\x88lji\xd5\xd8\xcd<\xca\xb7\xdb\x14\xe8k\xa8|\xf2@\x94\x0b\xdf\x95Ja\xb4\xbe\xd6\x8fS\xac\x98I\xf7"\xd0\xfe\xdfQ\xa2g\xe7\xd4\xa3\xb1\xa4F\x1a"\xf4\xd2\xf5\xd8t\x07O\xf8\xca\xfdh5am@\xa4\x96\x9f\xaa#s\x98z\xe8\x8cW\xea\xf5\xa8\x91\xd0\t\xf6\xeb\xc5}tx\x87\xcb\xef\x86\x8d\x12P\xb7\x160\x92\xf9wO\xd5\xc6\xa1\x1aq\x8e\x18\x00\x00\x00\xd4o\xd5a\xa6\xa3\xb7]\x00\x01\x96\x06\xe1\r\x00\x00-a1\xe1\xb1\xc4g\xfb\x02\x00\x00\x00\x00\x04YZ'

    # read the compressed df_cie1931 dataframe
    decompressed_df_cie1931 = io.BytesIO(lzma.decompress(compressed_df_cie1931))
    df_cie1931 = pd.read_pickle(decompressed_df_cie1931)

    # read the compressed df_intp_routes dataframe
    decompressed_df_intp_routes = io.BytesIO(lzma.decompress(compressed_df_intp_routes))
    df_intp_routes = pd.read_pickle(decompressed_df_intp_routes)

    # Create the scatter plot using Altair
    rect = alt.Chart(
        df_cie1931,      
        width=alt.Step(3), 
        height=alt.Step(3)
    ).transform_calculate(
        rgb="rgb(datum.color)"
    ).mark_rect(tooltip=True).encode(
        x=alt.X('x:N').axis(None),
        y=alt.Y('y:N').axis(None).scale(reverse=True),
        fill=alt.Fill('color').scale(None),
        stroke=alt.Stroke('color').scale(None),
        tooltip=[alt.Tooltip('color:N'), alt.Tooltip('rgb:N')]
    )

    line = alt.Chart(df_intp_routes).mark_line(
        tooltip=True, 
        interpolate='basis',
        strokeWidth=3
    ).encode(
        x='x:N',
        y='y:N',
        color=alt.Color('method')
            .scale(range=['#44aa99', '#994455', '#117733']),
        strokeDash=alt.StrokeDash('method'),
        order=alt.Order('index'),
        tooltip=[
            alt.Tooltip('color'),
            alt.Tooltip('x'),
            alt.Tooltip('y'), 
            alt.Tooltip('index')
        ]
    )

    (rect + line).configure_view(stroke=None)

In the color space are the trajectories of the blue/orange color
gradient overlayed based on the three interpolation methods
(``rgb``, ``hcl``, ``hcl-long``).
You can see that all interpolation methods chose a different route
in the color space. The "``rgb``" trajectory a direct route. The
``hcl`` trajectory is choosing a route on the bottom part of the space.
We now also understand why there is a ``-long`` suffix
in the interpolation method ``hcl-long``. 
The interpolation trajectory is indeed very ``long``.

The default interpolation between colors within Altair is ``hcl``. 
Dependening on your use-case you can choose another interpolation method,
for a complete list of interpolation options see :class:`ScaleInterpolateEnum`. 

Color-blind viewers
^^^^^^^^^^^^^^^^^^^
   
Around 8% of men and 0.5% of women have some form of color vision deficiency.
To make sure your visualizations are accessible to all viewers, it's
important to choose colors that are distinguishable even for those with 
color vision deficiencies. By using colors that have a high degree of
contrast, you can create visualizations that are not only informative but
also inclusive.

.. altair-plot::
    :hide-code:    
    :output: none

    color_vision_deficiency = {
        'redyellowblue': 9,
        'redyellowgreen' : 9
    }

.. list-table::
   :widths: 100
   :header-rows: 1

   * - Example
   * - **More friendly** diverging color scheme (``redyellowblue``). 
       This color scheme avoids using green colors, and instead uses red,
       yellow, and blue colors.

       .. altair-plot::
         :remove-code:

         plot_scheme("redyellowblue", color_vision_deficiency, cvd=True, continuous=True)

   * - **Unfriendly** diverging color scale (``redyellowgreen``).
       The red and green colors are used to represent different ends of a spectrum, 
       but these two colors are not easy differentiated with some type of CVD.

       .. altair-plot::
         :remove-code:

         plot_scheme("redyellowgreen", color_vision_deficiency, cvd=True, continuous=True)

Guidelines for using colors
^^^^^^^^^^^^^^^^^^^^^^^^^^^

While accuracy is the primary goal of visualizations, aesthetics also play
an important role in engaging viewers and making data more memorable.
By using a limited color palette, choosing harmonious colors, and balancing
colors to create a sense of visual hierarchy, you can create visualizations
that are not only informative but also visually attractive.

.. list-table::
   :widths: 50 50
   :header-rows: 1

   * - Intuitive colors 
     - Non-intuitive colors

   * - Choose colors that are easy to understand by selecting ones that
       naturally relate to your data.

       .. altair-plot::
         :hide-code:            
    
         source = pd.DataFrame({
             'land cover': ['Land', 'Water'],
             'value': [28, 55]
         })

         intuitive = alt.Chart(
             source, 
             height=alt.Step(80), 
             width=200
         ).mark_bar().encode(
             x=alt.X('value'),
             y=alt.Y('land cover'),
             color=alt.Color('land cover')
                 .scale(range=['#55AA22', '#5566AA'],
                        domain=['Land', 'Water'])
                 .legend(None)   
         )

         intuitive

     - It is confusing and difficult to understand if you choose
       colors which are non-intuive. Eg. green for water and blue for land.
       
       .. altair-plot::
         :hide-code:

         non_intuitive = alt.Chart(
             source, 
             height=alt.Step(80), 
             width=200
         ).mark_bar().encode(
             x=alt.X('value'),
             y=alt.Y('land cover'),
             color=alt.Color('land cover')
                 .scale(range=['#5566AA', '#55AA22'],
                        domain=['Land', 'Water'])
                 .legend(None)
         )

         non_intuitive


.. list-table::
   :widths: 50 50
   :header-rows: 1

   * - Colors in moderation
     - Colors in excess

   * - Try not to use too many colors. If you choose more colors, use them
       thoughtfully to emphasize the most important parts of your visualization.

       .. altair-plot::
         :hide-code:
    
         import altair as alt
         from vega_datasets import data

         source = data.barley.url

         labels = ["Crookston", "Grand Rapids"]

         cond_weight = alt.condition(
             alt.FieldOneOfPredicate(
                 field="value", oneOf=labels
             ),
             alt.value("bolder"),  # predicate True
             alt.value("normal"),  # predicate False
         )

         cond_color = alt.condition(
             alt.FieldOneOfPredicate(
                 field="site", oneOf=labels
             ),
             alt.value("#6A8AD5"),  # predicate True
             alt.value("#CCCCCC"),  # predicate False
         )

         moderate = (
             alt.Chart(source, width=200)
             .mark_bar()
             .encode(
                 x="sum(yield):Q",
                 y=alt.Y("site:N")
                 .sort("-x")
                 .axis(labelFontWeight=cond_weight),
                 color=cond_color,
             )
         )

         moderate

     - Using too many colors in graphs or charts can make them confusing
       and hard to read, which can lead to misunderstandings. To make it
       easy to understand, use colors carefully and don't use too many.

       .. altair-plot::
         :hide-code:

         excess = (
             alt.Chart(source, width=200)
             .mark_bar()
             .encode(
                 x="sum(yield):Q",
                 y=alt.Y("site:N").sort("-x"),
                 color=alt.Color("site:N")
                 .scale(scheme="set1")
                 .legend(None),
             )
         )

         excess


.. list-table::
   :widths: 50 50
   :header-rows: 1

   * - Consistency color usage between plots
     - In-consistent color usage between plots

   * - Using the same colors for the same data in charts or graphs helps
       people understand the information better.
       
       .. altair-plot::
         :hide-code:
    
         source = data.movies()
         
         line = (
             alt.Chart(source, width=200, height=200)
             .transform_fold(
                 fold=["US_Gross", "Worldwide_Gross"]
             )
             .mark_line()
             .encode(
                 x=alt.X("IMDB_Rating:Q").bin(True),
                 y=alt.Y("value:Q")
                 .aggregate("mean")
                 .sort("-x"),
                 color=alt.Color(
                     "key:N",
                     sort=["Worldwide_Gross"],
                 ).legend(
                     orient="top",
                     direction="horizontal",
                 ),
             )
         )
         
         bar = (
             alt.Chart(source, width=200)
             .transform_fold(
                 fold=["US_Gross", "Worldwide_Gross"]
             )
             .mark_bar()
             .encode(
                 x=alt.X("value:Q")
                 .aggregate("sum")
                 .title(None),
                 y=alt.Y("key:N").sort("-x"),
                 color=alt.Color(
                     "key:N",
                     sort=["Worldwide_Gross"],
                 )
                 .scale(range=["#6A8AD5", "#CCCCCC"])
                 .legend(
                     orient="top",
                     direction="horizontal",
                 ),
             )
         )
         
         equal = (line & bar).resolve_scale(
             color="shared"
         )
         equal

     - Choosing different colors for the same data can lead
       to misunderstandings or incorrect conclusions.
       
       .. altair-plot::
         :hide-code:

         inequal = (line & bar).resolve_scale(
             color="independent"
         )
         inequal



.. list-table::
   :widths: 50 50
   :header-rows: 1

   * - Clarity in colors
     - Indistinct color usage

   * - Use colors in order to make the data easier to read. If the items in the
       visualiation can be easily distinguished leads to better understanding of
       the data.
     
       .. altair-plot::
         :hide-code:
    
         source = data.stocks()

         col_range = [
             "#E69F00",
             "#57B4E9",
             "#019E73",
             "#F0E442",
             "#0072B2",
         ]
         col_sort = [
             "GOOG",
             "AAPL",
             "IBM",
             "AMZN",
             "MSFT",
         ]

         alt.Chart(
             source, width=200, height=200
         ).mark_line().encode(
             x="date:T",
             y=alt.Y("price:Q"),
             color=alt.Color(
                 "symbol:N", sort=col_sort
             ).scale(range=col_range),
         )

     - It is hard to understand the data correctly if you use colors
       that make the items in your visualization unclear from each other.
 
       ..  altair-plot::
         :hide-code:

         import altair as alt
         from vega_datasets import data

         source = data.stocks()

         alt.Chart(
             source, width=200, height=200
         ).mark_line().encode(
             x="date:T",
             y="price:Q",
             color=alt.Color("symbol:N").scale(
                 scheme="reds"
             ),
         )

.. list-table::
   :widths: 50 50
   :header-rows: 1

   * - Distinct classification of categories
     - No gradient colors for categories

   * - Often categories are unique and distinct from each other. 
       Emphasize this by chosing colors that are clearly distinct from each other.
       
       .. altair-plot::
         :hide-code:

         import altair as alt
         from vega_datasets import data

         source = data.stocks()
         col_range = [
             "#E69F00",
             "#57B4E9",
             "#019E73",
             "#F0E442",
             "#0072B2",
         ]
         col_sort = [
             "GOOG",
             "AAPL",
             "IBM",
             "AMZN",
             "MSFT",
         ]

         alt.Chart(
             source, width=200, height=200
         ).mark_bar().encode(
             x=alt.X('symbol:N', sort='-y'),
             y=alt.Y('price:Q').aggregate('sum'),
             color=alt.Color(
                 "symbol:N", sort=col_sort
             ).scale(range=col_range),
         )

     - When unique categories are not distinguishable by their color usage, 
       it can cause confusion and misunderstandings.

       .. altair-plot::
         :hide-code:

         source = data.stocks()

         alt.Chart(
             source, width=200, height=200
         ).mark_bar().encode(
             x=alt.X('symbol:N', sort=col_sort),
             y=alt.Y('price:Q').aggregate('sum'),
             color=alt.Color("symbol:N").scale(
                 scheme="purples"
             ),
         )

.. list-table::
   :widths: 50 50
   :header-rows: 1

   * - Explain colors using a colorbar
     - No understanding of used colors

   * - When you use colors in your visualization, it's important to explain
       what each color means so that people can understand your message better.
  
       .. altair-plot::
         :hide-code:

         import altair as alt
         from vega_datasets import data
         
         source = data.iowa_electricity()
         
         alt.Chart(
            source, width=200, height=200
         ).mark_area().encode(
             x="year:T",
             y="net_generation:Q",
             color=alt.Color("source:N").legend(
                orient="bottom",
                direction="horizontal",
                columns=2
             )
         )

     - If you do not explain what your colors mean, people might be confused
       and not understand your visualization properly. 
       
       .. altair-plot::
         :hide-code:

         import altair as alt
         from vega_datasets import data
         
         source = data.iowa_electricity()
         
         alt.Chart(
            source, width=200, height=200
         ).mark_area().encode(
             x="year:T",
             y="net_generation:Q",
             color=alt.Color("source:N").legend(
                None
             )
         )


Color schemes
~~~~~~~~~~~~~

This sections presents the three primary color schemes used in data
visualization: sequential, diverging, and categorical. 

Sequential schemes
^^^^^^^^^^^^^^^^^^

Sequential schemes are best suited for data that has an inherent ordering,
such as data that varies from low to high, or over time. Examples of
sequential data include temperature or population density, where the
range of values is continuous and unbroken.

.. altair-plot::
    :hide-code:    
    :output: none

    seqs_schemes = {
        "blues": 9,
        "tealblues": 9,
        "teals": 9,
        "greens": 9,
        "browns": 9,
        "greys": 9,
        "purples": 9,
        "warmgreys": 9,
        "reds": 9,
        "oranges": 9,
    }

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Scheme
     - Example
   * - .. code-block:: none
    
         blues

     - .. altair-plot::
         :remove-code:

         alt.vconcat(
             plot_scheme("blues", seqs_schemes, cvd=True, continuous=True, single=False, top=True),
             plot_scheme("blues", seqs_schemes, cvd=False, continuous=False, single=False, bottom=True)
         ).configure_concat(spacing=1).configure_view(stroke=None).resolve_scale(color='independent').configure_scale(rectBandPaddingInner=0.1)

   * - .. code-block:: none
    
         tealblues

     - .. altair-plot::
         :remove-code:

         alt.vconcat(
             plot_scheme("tealblues", seqs_schemes, cvd=True, continuous=True, single=False, top=True),
             plot_scheme("tealblues", seqs_schemes, cvd=False, continuous=False, single=False, bottom=True)
         ).configure_concat(spacing=1).configure_view(stroke=None).resolve_scale(color='independent').configure_scale(rectBandPaddingInner=0.1)

   * - .. code-block:: none
    
         teals

     - .. altair-plot::
         :remove-code:

         alt.vconcat(
             plot_scheme("teals", seqs_schemes, cvd=True, continuous=True, single=False, top=True),
             plot_scheme("teals", seqs_schemes, cvd=False, continuous=False, single=False, bottom=True)
         ).configure_concat(spacing=1).configure_view(stroke=None).resolve_scale(color='independent').configure_scale(rectBandPaddingInner=0.1)

   * - .. code-block:: none
    
         greens

     - .. altair-plot::
         :remove-code:

         alt.vconcat(
             plot_scheme("greens", seqs_schemes, cvd=True, continuous=True, single=False, top=True),
             plot_scheme("greens", seqs_schemes, cvd=False, continuous=False, single=False, bottom=True)
         ).configure_concat(spacing=1).configure_view(stroke=None).resolve_scale(color='independent').configure_scale(rectBandPaddingInner=0.1)

   * - .. code-block:: none
    
         browns

     - .. altair-plot::
         :remove-code:

         alt.vconcat(
             plot_scheme("browns", seqs_schemes, cvd=True, continuous=True, single=False, top=True),
             plot_scheme("browns", seqs_schemes, cvd=False, continuous=False, single=False, bottom=True)
         ).configure_concat(spacing=1).configure_view(stroke=None).resolve_scale(color='independent').configure_scale(rectBandPaddingInner=0.1)

   * - .. code-block:: none
    
         greys

     - .. altair-plot::
         :remove-code:

         alt.vconcat(
             plot_scheme("greys", seqs_schemes, cvd=True, continuous=True, single=False, top=True),
             plot_scheme("greys", seqs_schemes, cvd=False, continuous=False, single=False, bottom=True)
         ).configure_concat(spacing=1).configure_view(stroke=None).resolve_scale(color='independent').configure_scale(rectBandPaddingInner=0.1)

   * - .. code-block:: none
    
         purples

     - .. altair-plot::
         :remove-code:

         alt.vconcat(
             plot_scheme("purples", seqs_schemes, cvd=True, continuous=True, single=False, top=True),
             plot_scheme("purples", seqs_schemes, cvd=False, continuous=False, single=False, bottom=True)
         ).configure_concat(spacing=1).configure_view(stroke=None).resolve_scale(color='independent').configure_scale(rectBandPaddingInner=0.1)

   * - .. code-block:: none
    
         warmgreys

     - .. altair-plot::
         :remove-code:

         alt.vconcat(
             plot_scheme("warmgreys", seqs_schemes, cvd=True, continuous=True, single=False, top=True),
             plot_scheme("warmgreys", seqs_schemes, cvd=False, continuous=False, single=False, bottom=True)
         ).configure_concat(spacing=1).configure_view(stroke=None).resolve_scale(color='independent').configure_scale(rectBandPaddingInner=0.1)

   * - .. code-block:: none
    
         reds

     - .. altair-plot::
         :remove-code:

         alt.vconcat(
             plot_scheme("reds", seqs_schemes, cvd=True, continuous=True, single=False, top=True),
             plot_scheme("reds", seqs_schemes, cvd=False, continuous=False, single=False, bottom=True)
         ).configure_concat(spacing=1).configure_view(stroke=None).resolve_scale(color='independent').configure_scale(rectBandPaddingInner=0.1)

   * - .. code-block:: none
    
         oranges

     - .. altair-plot::
         :remove-code:

         alt.vconcat(
             plot_scheme("oranges", seqs_schemes, cvd=True, continuous=True, single=False, top=True),
             plot_scheme("oranges", seqs_schemes, cvd=False, continuous=False, single=False, bottom=True)
         ).configure_concat(spacing=1).configure_view(stroke=None).resolve_scale(color='independent').configure_scale(rectBandPaddingInner=0.1)

Diverging schemes
^^^^^^^^^^^^^^^^^

Diverging schemes are best suited for data that varies above and below a
center point, such as positive and negative deviations from a mean.
Examples of diverging data include measures of deviation, such as
temperature anomalies or changes in sea level.

.. altair-plot::
    :hide-code:    
    :output: none

    divg_schemes = {
        "blueorange": 9,
        "brownbluegreen": 9,
        "purplegreen": 9,
        "pinkyellowgreen": 9,
        "purpleorange": 9,
        "redblue": 9,
        "redgrey": 9,
        "redyellowblue": 9,
        "redyellowgreen": 9,
        "spectral": 9,
    }

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Scheme
     - Example
   * - .. code-block:: none
    
         blueorange

     - .. altair-plot::
         :remove-code:

         alt.vconcat(
             plot_scheme("blueorange", divg_schemes, cvd=True, continuous=True, single=False, top=True),
             plot_scheme("blueorange", divg_schemes, cvd=False, continuous=False, single=False, bottom=True)
         ).configure_concat(spacing=1).configure_view(stroke=None).resolve_scale(color='independent').configure_scale(rectBandPaddingInner=0.1)

   * - .. code-block:: none
    
         brownbluegreen

     - .. altair-plot::
         :remove-code:

         alt.vconcat(
             plot_scheme("brownbluegreen", divg_schemes, cvd=True, continuous=True, single=False, top=True),
             plot_scheme("brownbluegreen", divg_schemes, cvd=False, continuous=False, single=False, bottom=True)
         ).configure_concat(spacing=1).configure_view(stroke=None).resolve_scale(color='independent').configure_scale(rectBandPaddingInner=0.1)

   * - .. code-block:: none
    
         purplegreen

     - .. altair-plot::
         :remove-code:

         alt.vconcat(
             plot_scheme("purplegreen", divg_schemes, cvd=True, continuous=True, single=False, top=True),
             plot_scheme("purplegreen", divg_schemes, cvd=False, continuous=False, single=False, bottom=True)
         ).configure_concat(spacing=1).configure_view(stroke=None).resolve_scale(color='independent').configure_scale(rectBandPaddingInner=0.1)

   * - .. code-block:: none
    
         pinkyellowgreen

     - .. altair-plot::
         :remove-code:

         alt.vconcat(
             plot_scheme("pinkyellowgreen", divg_schemes, cvd=True, continuous=True, single=False, top=True),
             plot_scheme("pinkyellowgreen", divg_schemes, cvd=False, continuous=False, single=False, bottom=True)
         ).configure_concat(spacing=1).configure_view(stroke=None).resolve_scale(color='independent').configure_scale(rectBandPaddingInner=0.1)

   * - .. code-block:: none
    
         purpleorange

     - .. altair-plot::
         :remove-code:

         alt.vconcat(
             plot_scheme("purpleorange", divg_schemes, cvd=True, continuous=True, single=False, top=True),
             plot_scheme("purpleorange", divg_schemes, cvd=False, continuous=False, single=False, bottom=True)
         ).configure_concat(spacing=1).configure_view(stroke=None).resolve_scale(color='independent').configure_scale(rectBandPaddingInner=0.1)

   * - .. code-block:: none
    
         redblue

     - .. altair-plot::
         :remove-code:

         alt.vconcat(
             plot_scheme("redblue", divg_schemes, cvd=True, continuous=True, single=False, top=True),
             plot_scheme("redblue", divg_schemes, cvd=False, continuous=False, single=False, bottom=True)
         ).configure_concat(spacing=1).configure_view(stroke=None).resolve_scale(color='independent').configure_scale(rectBandPaddingInner=0.1)

   * - .. code-block:: none
    
         redgrey

     - .. altair-plot::
         :remove-code:

         alt.vconcat(
             plot_scheme("redgrey", divg_schemes, cvd=True, continuous=True, single=False, top=True),
             plot_scheme("redgrey", divg_schemes, cvd=False, continuous=False, single=False, bottom=True)
         ).configure_concat(spacing=1).configure_view(stroke=None).resolve_scale(color='independent').configure_scale(rectBandPaddingInner=0.1)

   * - .. code-block:: none
    
         redyellowblue

     - .. altair-plot::
         :remove-code:

         alt.vconcat(
             plot_scheme("redyellowblue", divg_schemes, cvd=True, continuous=True, single=False, top=True),
             plot_scheme("redyellowblue", divg_schemes, cvd=False, continuous=False, single=False, bottom=True)
         ).configure_concat(spacing=1).configure_view(stroke=None).resolve_scale(color='independent').configure_scale(rectBandPaddingInner=0.1)

   * - .. code-block:: none
    
         redyellowgreen

     - .. altair-plot::
         :remove-code:

         alt.vconcat(
             plot_scheme("redyellowgreen", divg_schemes, cvd=True, continuous=True, single=False, top=True),
             plot_scheme("redyellowgreen", divg_schemes, cvd=False, continuous=False, single=False, bottom=True)
         ).configure_concat(spacing=1).configure_view(stroke=None).resolve_scale(color='independent').configure_scale(rectBandPaddingInner=0.1)

   * - .. code-block:: none
    
         spectral

     - .. altair-plot::
         :remove-code:

         alt.vconcat(
             plot_scheme("spectral", divg_schemes, cvd=True, continuous=True, single=False, top=True),
             plot_scheme("spectral", divg_schemes, cvd=False, continuous=False, single=False, bottom=True)
         ).configure_concat(spacing=1).configure_view(stroke=None).resolve_scale(color='independent').configure_scale(rectBandPaddingInner=0.1)

Cyclical schemes
^^^^^^^^^^^^^^^^

Cyclical color schemes may be used to highlight periodic patterns in continuous data.
However, these schemes are not well suited to accurately convey value differences.

.. altair-plot::
    :hide-code:    
    :output: none

    cycl_schemes = {
        "rainbow": 9,
        "sinebow": 9
    }

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Scheme
     - Example
   * - .. code-block:: none
    
         rainbow

     - .. altair-plot::
         :remove-code:

         alt.vconcat(
             plot_scheme("rainbow", cycl_schemes, cvd=True, continuous=True, single=False, top=True),
             plot_scheme("rainbow", cycl_schemes, cvd=False, continuous=False, single=False, bottom=True)
         ).configure_concat(spacing=1).configure_view(stroke=None).resolve_scale(color='independent').configure_scale(rectBandPaddingInner=0.1)

   * - .. code-block:: none
    
         sinebow

     - .. altair-plot::
         :remove-code:

         alt.vconcat(
             plot_scheme("sinebow", cycl_schemes, cvd=True, continuous=True, single=False, top=True),
             plot_scheme("sinebow", cycl_schemes, cvd=False, continuous=False, single=False, bottom=True)
         ).configure_concat(spacing=1).configure_view(stroke=None).resolve_scale(color='independent').configure_scale(rectBandPaddingInner=0.1)

Categorical schemes
^^^^^^^^^^^^^^^^^^^

Categorical schemes are best suited for data that is unordered, such as
different species or categories. Examples of categorical data include
the types of flowers in a garden, or different political affiliations.

.. altair-plot::
    :hide-code:    
    :output: none

    catg_schemes = {
        "accent": 8,
        "category10": 10,
        "category20": 20,
        "category20b": 20,
        "category20c": 20,
        "dark2": 8,
        "paired": 12,
        "pastel1": 9,
        "pastel2": 8,
        "set1": 9,
        "set2": 8,
        "set3": 12,
        "tableau10": 10,
        "tableau20": 20,
    }

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Scheme
     - Example
   * - .. code-block:: none
    
         accent

     - .. altair-plot::
         :remove-code:

         plot_scheme("accent", catg_schemes, cvd=True, continuous=False).configure_scale(rectBandPaddingInner=0.1)

   * - .. code-block:: none
    
         category10

     - .. altair-plot::
         :remove-code:

         plot_scheme("category10", catg_schemes, cvd=True, continuous=False).configure_scale(rectBandPaddingInner=0.1)

   * - .. code-block:: none
    
         category20

     - .. altair-plot::
         :remove-code:

         plot_scheme("category20", catg_schemes, cvd=True, continuous=False).configure_scale(rectBandPaddingInner=0.1)

   * - .. code-block:: none
    
         category20b

     - .. altair-plot::
         :remove-code:

         plot_scheme("category20b", catg_schemes, cvd=True, continuous=False).configure_scale(rectBandPaddingInner=0.1)

   * - .. code-block:: none
    
         category20c

     - .. altair-plot::
         :remove-code:

         plot_scheme("category20c", catg_schemes, cvd=True, continuous=False).configure_scale(rectBandPaddingInner=0.1)

   * - .. code-block:: none
    
         dark2

     - .. altair-plot::
         :remove-code:

         plot_scheme("dark2", catg_schemes, cvd=True, continuous=False).configure_scale(rectBandPaddingInner=0.1)

   * - .. code-block:: none
    
         paired

     - .. altair-plot::
         :remove-code:

         plot_scheme("paired", catg_schemes, cvd=True, continuous=False).configure_scale(rectBandPaddingInner=0.1)

   * - .. code-block:: none
    
         pastel1

     - .. altair-plot::
         :remove-code:

         plot_scheme("pastel1", catg_schemes, cvd=True, continuous=False).configure_scale(rectBandPaddingInner=0.1)

   * - .. code-block:: none
    
         pastel2

     - .. altair-plot::
         :remove-code:

         plot_scheme("pastel2", catg_schemes, cvd=True, continuous=False).configure_scale(rectBandPaddingInner=0.1)

   * - .. code-block:: none
    
         set1

     - .. altair-plot::
         :remove-code:

         plot_scheme("set1", catg_schemes, cvd=True, continuous=False).configure_scale(rectBandPaddingInner=0.1)

   * - .. code-block:: none
    
         set2

     - .. altair-plot::
         :remove-code:

         plot_scheme("set2", catg_schemes, cvd=True, continuous=False).configure_scale(rectBandPaddingInner=0.1)

   * - .. code-block:: none
    
         set3

     - .. altair-plot::
         :remove-code:

         plot_scheme("set3", catg_schemes, cvd=True, continuous=False).configure_scale(rectBandPaddingInner=0.1)

   * - .. code-block:: none
    
         tableau10

     - .. altair-plot::
         :remove-code:

         plot_scheme("tableau10", catg_schemes, cvd=True, continuous=False).configure_scale(rectBandPaddingInner=0.1)

   * - .. code-block:: none
    
         tableau20

     - .. altair-plot::
         :remove-code:

         plot_scheme("tableau20", catg_schemes, cvd=True, continuous=False).configure_scale(rectBandPaddingInner=0.1)

Palettes from other sources
~~~~~~~~~~~~~~~~~~~~~~~~~~~

This subsection focuses on pre-designed color palettes that can be
used in data visualization from other sources.

Here some color schemes from Paul Tol, https://personal.sron.nl/~pault/ which are picked as being:

- distinct for all people, including colour-blind readers
- distinct from black and white
- distinct on screen and paper
- matching well together

.. altair-plot::   
    :output: none

    tol_schemes = {
        "tol_bright" : ['#4477AA', '#EE6677', '#228833', '#CCBB44', '#66CCEE', '#AA3377', '#BBBBBB'],
        "tol_highcontrast" : ['#FFFFFF', '#DDAA33', '#BB5566', '#004488', '#000000'],
        "tol_vibrant": ['#0077BB', '#33BBEE', '#009988', '#EE7733', '#CC3311', '#EE3377', '#BBBBBB'],
        "tol_muted": ['#332288', '#88CCEE', '#44AA99', '#117733', '#999933', '#DDCC77' ,'#CC6677' , '#882255', '#AA4499', '#DDDDDD'],
        "tol_mediumcontrast": ['#FFFFFF', '#EECC66', '#994455','#6699CC', '#997700', '#994455', '#004488', '#000000'],
        "tol_pale": ['#BBCCEE', '#CCEEFF', '#CCDDAA', '#EEEEBB', '#FFCCCC', '#DDDDDD'],
        "tol_dark": ['#222255', '#225555', '#225522', '#666633', '#663333', '#555555'],
        "tol_light": ['#77AADD', '#99DDFF', '#44BB99', '#BBCC33', '#AAAA00', '#EEDD88', '#EE8866', '#FFAABB', '#DDDDDD'],
        "tol_sunset": ['#364B9A', '#4A7BB7', '#6EA6CD', '#98CAE1', '#C2E4EF', '#EAECCC', '#FEDA8B', '#FDB366', '#F67E4B', '#DD3D2D', '#A50026'],
        "tol_nightfall": ['#125A56', '#00767B', '#238F9D', '#42A7C6', '#60BCE9', '#9DCCEF', '#C6DBED', '#DEE6E7', '#ECEADA', '#F0E6B2', '#F9D576', '#FFB954', '#FD9A44', '#F57634', '#E94C1F', '#D11807', '#A01813'],
        "tol_PRGn": ['#762A83', '#9970AB', '#C2A5CF', '#E7D4E8', '#F7F7F7', '#D9F0D3', '#ACD39E', '#5AAE61', '#1B7837'],
        "tol_YlOrBr": ['#FFFFE5', '#FFF7BC', '#FEE391', '#FEC44F', '#FB9A29', '#EC7014', '#CC4C02', '#993404', '#662506'],
        "tol_iridescent": ['#FEFBE9', '#FCF7D5', '#F5F3C1', '#EAF0B5', '#DDECBF', '#D0E7CA', '#C2E3D2', '#B5DDD8', '#A8D8DC', '#9BD2E1', '#8DCBE4', '#81C4E7', '#7BBCE7', '#7EB2E4', '#88A5DD', '#9398D2', '#9B8AC4', '#9D7DB2', '#9A709E', '#906388', '#805770', '#684957', '#46353A'],
        "tol_incandescent": [ '#CEFFFF', '#C6F7D6', '#A2F49B', '#BBE453', '#D5CE04', '#E7B503', '#F19903', '#F6790B', '#F94902', '#E40515', '#A80003']        
    }

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Scheme
     - Example
   * - .. code-block:: none
    
         tol_bright

     - .. altair-plot::
         :remove-code:

         plot_scheme("tol_bright", tol_schemes, cvd=True, continuous=False, grayscale=True).configure_scale(rectBandPaddingInner=0.1)

   * - .. code-block:: none
    
         tol_highcontrast

     - .. altair-plot::
         :remove-code:

         plot_scheme("tol_highcontrast", tol_schemes, cvd=True, continuous=False, grayscale=True).configure_scale(rectBandPaddingInner=0.1)

   * - .. code-block:: none
    
         tol_vibrant

     - .. altair-plot::
         :remove-code:

         plot_scheme("tol_vibrant", tol_schemes, cvd=True, continuous=False, grayscale=True).configure_scale(rectBandPaddingInner=0.1)

   * - .. code-block:: none
    
         tol_muted

     - .. altair-plot::
         :remove-code:

         plot_scheme("tol_muted", tol_schemes, cvd=True, continuous=False, grayscale=True).configure_scale(rectBandPaddingInner=0.1)

   * - .. code-block:: none
    
         tol_mediumcontrast

     - .. altair-plot::
         :remove-code:

         plot_scheme("tol_mediumcontrast", tol_schemes, cvd=True, continuous=False, grayscale=True).configure_scale(rectBandPaddingInner=0.1)

   * - .. code-block:: none
    
         tol_pale

     - .. altair-plot::
         :remove-code:

         plot_scheme("tol_pale", tol_schemes, cvd=True, continuous=False, grayscale=True).configure_scale(rectBandPaddingInner=0.1)

   * - .. code-block:: none
    
         tol_dark

     - .. altair-plot::
         :remove-code:

         plot_scheme("tol_dark", tol_schemes, cvd=True, continuous=False, grayscale=True).configure_scale(rectBandPaddingInner=0.1)

   * - .. code-block:: none
    
         tol_light

     - .. altair-plot::
         :remove-code:

         plot_scheme("tol_light", tol_schemes, cvd=True, continuous=False, grayscale=True).configure_scale(rectBandPaddingInner=0.1)
         
   * - .. code-block:: none
    
         tol_light

     - .. altair-plot::
         :remove-code:

         plot_scheme("tol_light", tol_schemes, cvd=True, continuous=False, grayscale=True).configure_scale(rectBandPaddingInner=0.1)

   * - .. code-block:: none
    
         tol_sunset

     - .. altair-plot::
         :remove-code:

         plot_scheme("tol_sunset", tol_schemes, cvd=True, continuous=True, grayscale=True)

   * - .. code-block:: none
    
         tol_nightfall

     - .. altair-plot::
         :remove-code:

         plot_scheme("tol_nightfall", tol_schemes, cvd=True, continuous=True, grayscale=True)

   * - .. code-block:: none
    
         tol_iridescent

     - .. altair-plot::
         :remove-code:

         plot_scheme("tol_iridescent", tol_schemes, cvd=True, continuous=True, grayscale=True)

   * - .. code-block:: none
    
         tol_incandescent

     - .. altair-plot::
         :remove-code:

         plot_scheme("tol_incandescent", tol_schemes, cvd=True, continuous=True, grayscale=True)

Expressions and colors
~~~~~~~~~~~~~~~~~~~~~~

We can make use of the measured values regarding colors in a visualization.
In the following example we will make use of the ``lumniance`` to detect if 
the color of a text overlay on top of a bar should be colored ``black`` or
``white``. The luminance describes the brightnes, normalized to 0 for darkest
black and 1 for lightest white.

In the following chart we have a sorted bar chart where the text overlay describes
the sum of yield as is expressed on the ``x`` encoding channel.

.. altair-plot::

    import altair as alt
    from vega_datasets import data

    source = data.barley()

    base = alt.Chart(source).encode(
        x=alt.X('sum(yield):Q').stack('zero'),
        y=alt.Y('site:O').sort('-x'),
        text=alt.Text('sum(yield):Q', format='.0f')
    )

    bars = base.mark_bar().encode(color='sum(yield):Q')
    text = base.mark_text(align='right', dx=-3, color='black')

    bars + text

As you can see, when the bar becomes darker, the text overlay becomes less visible.

At this moment we can make use of the measured luminance to decide if the text overlay
should be colored ``black`` or ``white``.

.. altair-plot::

    import altair as alt
    from vega_datasets import data

    source = data.barley()

    base = alt.Chart(source).encode(
        x=alt.X('sum(yield):Q').stack('zero'),
        y=alt.Y('site:O').sort('-x'),
        text=alt.Text('sum(yield):Q', format='.0f')
    )

    bars = base.mark_bar(
        tooltip=alt.expr("luminance(scale('color', datum.sum_yield))")
    ).encode(
        color='sum(yield):Q'
    )

    text = base.mark_text(
        align='right', 
        dx=-3,
        color=alt.expr("luminance(scale('color', datum.sum_yield)) > 0.5 ? 'black' : 'white'")
    )

    bars + text

The lighter the bar, the higher the luminance. If the bar is light
we like a text overlay that is black. The darker the bar, the lower
the luminance. If the bar is dark, we like a text overlay that is white.

In the expression above we have written this as a predicate. The text
appear ``black`` if the luminance is above ``0.5`` and ``white`` when
the luminance is below ``0.5``. The luminance is computed using the
``'color'`` scale in combination with the interal computed data field
``datum.sum_yield``. You can inspect the luminance through the tooltip
by hovering the bars.

Conclusion
~~~~~~~~~~

If you use the right colors when making visualizations with scientific
data, you can make them look good and easy to understand. You can use
pre-designed color schemes or choose your own, but make sure they look
good, are easy to see and make sense with the information you're
presenting.