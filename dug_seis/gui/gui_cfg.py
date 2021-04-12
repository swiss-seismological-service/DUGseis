"""
Defines the structure of the GUI and the mapping to the
data structure of the processing part of the program defined in dug-seis-default.yaml.

The order of the widgets in the GUI is defined by the order here in param_gui.


description     creates a tooltip at the label
items           options of a QComboBox
is_switching    if existing: QComboBox that chooses one of several QGroupBox elements
has_children    if existing: necessary for all levels but the deepest
is_group        if existing: will create a QGroupBox element as parent widget
hidden          if existing: element and all children will not be in the GUI
widget_type     optional; default = QLineEdit
height          in pixel


Headings can be added to create single line labels without input element.
Example:
    'heading-coordinate-system': {
        'caption':      'Origin of local coordinate system',
        'is_heading':   True,
    },


The following parameter are treated differently:
– General.sensor_coords
– Acquisition.gain_selection
– Trigger.channels


"""
elem_tree = {}

# param_tree['General']['operator'] = elem_tree['General']['operator'].val()


# Params not to be displayed
param_hidden = [
    ('Channels', 'station_naming'),
]


param_gui = {
    'General': {
        'has_children':   True,

        'project_name': {
            'caption':      'Project name',
        },
        'project_location': {
            'caption':      'Project location',
        },
        'operator': {
            'caption':      'Operator',
            'widget_type':  'QTextEdit',
        },
        'project_description': {
            'caption':      'Project description',
            'widget_type':  'QTextEdit',
            'height':       100,
        },
        'acquisition_folder': {
            'caption':      'Acquisition Folder',
            'widget_type':  'QTextEdit',
        },
        'processing_folder': {
            'caption':      'Processing Folder',
            'widget_type':  'QTextEdit',
        },
        'asdf_folder': {
            'caption':      'ASDF folder',
            'widget_type':  'QTextEdit',
            'description':  (
                ('folder with ASDF files used for <b>Processing</b>; is normally ' +
                '(but not necessarily!) the same as “Acquisition Folder”')
            ),
        },
        'sensor_count': {
            'caption':      'Sensor count',
        },
        # -> in Channels tab
        # 'sensor_coords': {
        #     'caption':      'Sensor coordinates',
        # },
        'active_trigger_channel': {
            'hidden' :      True,
            'caption':      'Active trigger channel',
        },
        'vs': {
            'caption':      'v<sub>p</sub> [m/s]',
            'description':  (
                'P-wave velocity<br>' +
                'Used for localization or hypocenters.'
            ),
        },
        'vp': {
            'caption':      'v<sub>s</sub> [m/s]',
            'description':  (
                'S-wave velocity<br>' +
                'Used for localization or hypocenters.'
            ),
        },
        'heading-coordinate-system': {
            'caption':      'Origin of local coordinate system',
            'is_heading':   True,
        },
        'origin_ch1903_east': {
            'caption':      'ch1903 easting',
        },
        'origin_ch1903_north': {
            'caption':      'ch1903 northing',
        },
        'origin_elev': {
            'caption':      'Elevation',
        },
        'stats': {
            'has_children':   True,
            'caption':        'Stats',

            'network': {
                'caption':      'Network',
            },
        },
    },
    'Sensors': {
        'has_children':   True,

        # 'sensor_coords': {
        #     'caption':      'Sensor coordinates',
        #     'breadcrumb':   ('General', 'sensor_coords'),
        # },
    },
    'Acquisition': {
        'has_children':   True,

        'hardware_settings': {
            'has_children':   True,
            'caption':        'Hardware settings',
            'vertical_resolution': {
                'caption':      'Vertical resolution [Bit]',
                'widget_type':  'QComboBox',
                'items':        ['14', '16', '20'],
            },
            'sampling_frequency': {
                'caption':      'Sampling frequency [Hz]',
                'widget_type':  'QComboBox',
                'items':        ['100000', '200000', '500000', '1000000'],
            },
            # -> in Channels tab
            # 'input_range': {
            #     # TODO  Is that correct?
            #     'caption':      'Input range',
            # },
        },
        'asdf_settings': {
            'has_children':   True,
            'caption':        'ASDF settings',

            'save_mV': {
                'caption':      'Use float32',
                'widget_type':  'QCheckBox',
            },
            'compression': {
                'caption':      'Compression',
                'widget_type':  'QComboBox',
                'items':        ['None', 'gzip-0', 'gzip-2', 'gzip-3', 'gzip-3', 'gzip-4', 'gzip-5', 'gzip-6', 'gzip-7', 'gzip-8', 'gzip-9'],
            },
            'file_length_sec': {
                'caption':      'File length [sec]',
                'description':  (
                    'The recording time of each data file<br>' +
                    '(snippet). Normally set between<br>' +
                    '5 and 30 seconds.'),
            },
            'station_naming': {
                'hidden' :      True,
                'caption':      'Station naming',
            },
        },
    },
    'Trigger': {
        'has_children':   True,

        # -> in Channels tab
        # 'channels': {
        #     'caption':      'Channels',
        # },
        'input_range_source': {
            'caption':      'Input range source',
            'widget_type':  'QComboBox',
            'items':        ['YAML', 'ASDF'],
            # 'description': '',
        },
        'bandpass_f_min': {
            'caption':      'Bandpass freq. min [Hz]',
            'description':  'Applied before triggering',
        },
        'bandpass_f_max': {
            'caption':      'Bandpass freq. max [Hz]',
            'description':  'Applied before triggering',
        },
        'coincidence': {
            'caption':  'Coincidence',
            'description':
                ('The coincidence used for triggering <br>' +
                'in the recursive STA LTA algorithm. If<br>' +
                'the coincidence is set to for example 3,<br>' +
                'this effectively tells the trigger to only<br>' +
                'go off and register an event if there are<br>' +
                'at least arrivals registered at 3 or more<br>' +
                'traces.'
            ),
        },
        'heading-trigger-params': {
            'caption':      'Parameters of STA/LTA trigger are set in Tab „Sensors“',
            'is_heading':   True,
        },
        # -> in Channels tab
        # 'algorithm': {
        #     'caption':      'Algorithm',
        #     'widget_type':  'QComboBox',
        #     'items':        ['recstalta'],
        #     'is_switching': False
        # },
        # 'recstalta': {
        #     'has_children':   True,
        #     'is_group':       True,
        #     # 'caption':        'STA LTA',
        #     'caption':        '',

        #     'threshold_on': {
        #         'caption':      'Threshold on',
        #     },
        #     'threshold_off': {
        #         'caption':      'Threshold off',
        #     },
        #     'st_window': {
        #         'caption':      'ST window [samples]',
        #     },
        #     'lt_window': {
        #         'caption':      'LT window [samples]',
        #     },
        # },
        'offset': {
            'caption':      'Offset',
            'description':  'Time interval for picking, offset',
        },
        'interval_length': {
            'caption':      'Interval length [ms]',
            'description':  'Time interval for picking, length',
        },
        'classification': {
            'hidden' :          True,
            'has_children':     True,
            'caption':          'Classification',

            'spread_int': {
                'caption':      'Spread interval',
                'description':  (
                    'The maximum time between the first and the<br>' +
                    'last moment of triggering at different stations<br>' +
                    'for which this event is classified as electronic<br>' +
                    'interference. in seconds. Normally set to 0.25e-2.'
                ),
            },
        },
        'time_between_events': {
            'caption':      'Time between events [s]',
            'description':  (
                'The empty time in seconds that has to exist between 2 different<br>' +
                'events. For example set to 0.0006 seconds. The purpose of<br>' +
                'this parameter is to make sure that a single event is not recognized<br>' +
                'as 2 separate events. If the parameter is chosen too high 2 separate<br>' +
                ' events may be recognized as a single event.'
            )
        },
    },
    'Processing': {
        'has_children':     True,

        'heading-proc-contin': {
            'caption':      'Continuous processing',
            'is_heading':   True,
            'is_bold':      True,
        },
        'proc_start_time': {
            'caption':      'Start time',
            'description':  (
                'Date and time (optional) from which to start processing.<br>' +
                'Arbitrary delimiters, missing digits will be set to zeroes.<br>' +
                'Examples:<br>' +
                '2017-02-09<br>' +
                '2017-02-09T13:27<br>' +
                '2017-02-09_13:27:05.225343<br>' +
                '2017-02-09-13-27-05.225_343'
            ),
        },
        'parallel_processing': {
            'caption':      'Parallel processing',
            'widget_type':  'QCheckBox',
        },
        'number_workers': {
            'caption':      'Number of workers',
            'description':  'Number of events to be processed at the same time.',
        },
        'wait_for_new_data': {
            'caption':      'Wait for new data',
            'widget_type':  'QCheckBox',
            'description':  'Number of events to be processed at the same time.',
        },

        'heading-proc-plotting': {
            'caption':      'Plotting',
            'is_heading':   True,
            'is_bold':      True,
        },
        'bandpass_f_min': {
            'caption':      'Band/highpass min freq. [Hz]',
            'type':         'int_or_None',
            'description':  'Leave empty for lowpass filter.',
        },
        'bandpass_f_max': {
            'caption':      'Band/lowpass max freq. [Hz]',
            'type':         'int_or_None',
            'description':  'Leave empty for highpass filter.',
        },
        'channels_selector': {
            'function':     'create_channels_selector',
        },
        'spectro': {
            'has_children':     True,
            'is_group':         True,
            'caption':          'Spectrum',

            'spectro_show': {
                'caption':      'Show spectrum',
                'widget_type':  'QCheckBox',
            },
            'spectro_logx': {
                'caption':      'x axis logarithmic',
                'widget_type':  'QCheckBox',
            },
            'spectro_start_pick': {
                'caption':      'Start point at pick',
                'widget_type':  'QCheckBox',
                'description':  'Use P-wave pick time as start point of the interval for the calculation of the spectrum'
            },
        },
        'heading-proc-plotting_periodic': {
            'caption':      'Periodic plotting',
            'is_heading':   True,
        },
        'periodic_plotting': {
            'caption':      'Event plot',
            'widget_type':  'QCheckBox',
            'description':  'If checked, waveforms are periodically plotted.',
        },
        'periodic_plotting_interval': {
            'caption':      'Event plot, interval [s]',
        },
        'noise_vis': {
            'caption':      'Background noise plot',
            'widget_type':  'QCheckBox',
        },
        'noise_vis_interval': {
            'caption':      'Noise plot every n-th plot',
            # 'description':  (
            #     'The interval between noise visualizations<br>' +
            #     'being generated in seconds. Normally set to 300,<br>' +
            #     'which means that every 300 seconds a plot of all traces<br>' +
            #     '(filled with noise) is generated without any trigger<br>' +
            #     'having gone off.'
            # )
        },
        'heading-proc-single_plot': {
            'caption':      'Single plot',
            'is_heading':   True,
        },
        'single_plot_time': {
            'caption':      'Time',
            'description':  (
                'Date and time (optional) from which to start plotting.<br>' +
                'Arbitrary delimiters, missing digits will be set to zeroes.<br>' +
                'Examples:<br>' +
                '2017-02-09<br>' +
                '2017-02-09T13:27<br>' +
                '2017-02-09_13:27:05.225343<br>' +
                '2017-02-09-13-27-05.225_343'
            ),
        },
        'single_plot_reprocess': {
            'caption':      'Reprocess',
            'widget_type':  'QCheckBox',
            'description':  'If checked, perform processing: picking, locating, …',
        },
    },

    'Picking': {
        'has_children':     True,
        'algorithm': {
            'caption':      'Algorithm',
            'widget_type':  'QComboBox',
            'items':        ['sta_lta'],
            'is_switching': True,
        },
        's_picking': {
            'caption':      'S picking',
            'widget_type':  'QCheckBox',
        },

        'sta_lta': {
            'has_children':     True,
            'is_group':         True,
            'caption':          'STA/LTA',
            # 'caption':        '',
            'p_wave': {
                'has_children':     True,
                'is_group':         True,
                'caption':          'P-Wave Picker',

                'bandpass_f_min': {
                    'caption':      'Bandpass min Freq. [Hz]',
                },
                'bandpass_f_max': {
                    'caption':      'Bandpass max Freq. [Hz]',
                },
                # 'algorithm': {
                #     'caption':      'Algorithm',
                #     'widget_type':  'QComboBox',
                #     'items':        ['sta_lta'],
                #     'is_switching': True,
                # },

                'threshold_on': {
                    'caption':      'Threshold on',
                    'description':  'The threshold for starting of triggering.',
                },
                'threshold_off': {
                    'caption':      'Threshold off',
                    'description':  'The threshold for stopping of triggering.',
                },
                'st_window': {
                    'caption':      'ST window [samples]',
                },
                'lt_window': {
                    'caption':      'LT window [samples]',
                },
            },

            's_wave': {
                'has_children':     True,
                'is_group':         True,
                'caption':          'S-Wave Picker',

                'gap': {
                    'caption':      'Gap [ms]',
                    # 'description':  '',
                },
                'length': {
                    'caption':      'Length [ms]',
                    # 'description':  '',
                },
                'bandpass_f_min': {
                    'caption':      'Bandpass min Freq. [Hz]',
                },
                'bandpass_f_max': {
                    'caption':      'Bandpass max Freq. [Hz]',
                },

                'threshold_on': {
                    'caption':      'Threshold on',
                    'description':  'The threshold for starting of triggering.',
                },
                'threshold_off': {
                    'caption':      'Threshold off',
                    'description':  'The threshold for stopping of triggering.',
                },
                'st_window': {
                    'caption':      'ST window [samples]',
                },
                'lt_window': {
                    'caption':      'LT window [samples]',
                },
            },
            # 'aicd': {
            #     'has_children':   True,
            #     'is_group':       True,
            #     'caption':        'AICD',
            #     'bandpass_f_min': {
            #         'caption':      'Bandpass min Freq. [Hz]',
            #     },
            #     'bandpass_f_max': {
            #         'caption':      'Bandpass max Freq. [Hz]',
            #     },
            #     't_ma [ms]': {
            #         'caption':      'T<sub>ma</sub>',
            #     },
            #     'nsigma': {
            #         'caption':      'n<sub>σ</sub>',
            #     },
            #     't_up [ms]': {
            #         'caption':      't<sub>up</sub>',
            #     },
            #     'nr_len': {
            #         'caption':      'nr length',
            #     },
            #     'nr_coeff': {
            #         'caption':      'nr coeff.',
            #     },
            #     'pol_len': {
            #         'caption':      'pol length',
            #     },
            #     'pol_coeff': {
            #         'caption':      'pol coeff.',
            #     },
            #     'uncert_coeff': {
            #         'caption':      'uncert. coeff',
            # },
            # 'pphase': {
            #     'has_children':   True,
            #     'is_group':       True,
            #     # 'caption':        'P-Phase',
            #     'caption':        '',

            #     'Tn': {
            #         'caption':      'T<sub>n</sub>',
            #     },
            #     'xi': {
            #         'caption':      'x<sub>i</sub>',
            #     },
            # },
        },
    },

    'Loc_Mag': {
        'has_children':     True,

        'Locate': {
            'has_children':     True,
            'caption':          'Locate',

            'min_picks': {
                'caption':      'Min picks',
                'description':  (
                    'The minimum number of picks at<br>' +
                    'different stations necessary<br>' +
                    'for one event for hypocenter<br>' +
                    'localization to be done.<br>' +
                    'Normally set to 6.'
                ),
            },
            'damping': {
                'caption':      'Damping',
            },
            'algorithm': {
                'caption':      'Algorithm',
                'widget_type':  'QComboBox',
                'items':        ['hom_iso', 'hom_aniso'],
                'description':  'The algorithm used for hypocenter localization.',
            },
            'hom_aniso': {
                'has_children':     True,
                'is_group':         True,
                # 'caption':          'hom_aniso',
                'caption':          '',

                'vp_min': {
                    'caption':      'v<sub>p, min</sub>',
                },
                'epsilon': {
                    'caption':      'Thomsen ε',
                },
                'delta': {
                    'caption':      'Thomsen δ',
                },
                'heading-anisotr-vect': {
                    'caption':      'Anisotropy vector',
                    'is_heading':   True,
                },
                'azi': {
                    'caption':      'Azimuth [°]',
                },
                'inc': {
                    'caption':      'Inclination [°]',
                },
            },
        },
        'Magnitude': {
            'has_children':     True,
            'caption':          'Magnitude',

            'bandpass_f_min': {
                'caption':      'Bandpass freq. min [Hz]',
                'description':  'Applied before triggering',
            },
            'bandpass_f_max': {
                'caption':      'Bandpass freq. max [Hz]',
                'description':  'Applied before triggering',
            },
            'algorithm': {
                'caption':      'Algorithm',
                'widget_type':  'QComboBox',
                'items':        ['relative'],
            },
            'q': {
                'caption':      'q',
                # 'description':   '',
            },
            'r0': {
                'caption':      'r<sub>0</sub>',
                'description':  'Distance',
            },
            'f0': {
                'caption':      'f<sub>0</sub>',
                'description':  'Correction frequency',
            },
        },
    },

#   Folders:
#     quakeml_folder            : events
#     plot_folder_active        : event_figs_active
#     plot_folder_passive       : event_figs_passive
#     plot_folder_electronic    : event_figs_electronic
#     noise_vis_folder          : noise_vis

    # 'Merge': {
    #     'merge_time_sec': {
    #         'caption':      'Merge time [s]',
    #     },
    #     'merge_folder': {
    #         'caption':      'Merge folder',
    #     },
    # },
}


help_content = [
    ['heading1', 'General Information'],
    ['text', 'Some labels show a <b>tooltip</b> text when the pointer hovers over them.'],
    ['text', 'Don’t close the program before acquisition and processing are stopped, and all processes have terminated.'],


    ['heading1', 'Sections'],
    ['text', '<b>Shortcuts</b>'],
    ['text', 'Activate all sections with <code>Ctrl + </code> first letter.'],
    ['text', 'Exception: Activate „Picker“ with <code>Ctrl + K</code>.'],
    ['text', '<code>F11</code> Toggle fullscreen'],

    ['heading2', 'Processing'],
    ['text', 'After clicking “Stop Processing” all triggered times of the current ASDF file continue being processed.'],

    ['heading3', 'Spectrum'],
    ['text', 'Only 2048 samples are used to calculate the spectrum. Start point of this interval is normally the first sample of the plot.'],
    ['text', 'If the option <b>Start point at pick</b> is activated, spectrum plots of channels that don’t include a P-wave pick are marked with a „*“ after the channel number.'],

    ['heading3', 'Single plot'],
    ['text', '<b>Reprocess</b> If checked, picks, etc. are calculated with the current paramater values.<br>If not checked, used with events: previously calculated results are displayed.'],


    ['heading1', 'Plot'],
    ['text', '<b>Red lines</b>: P-Wave pick time'],
    ['text', '<b>Cyan dasheddotted lines</b>: S-Wave pick time'],
    ['text', '<b>Green dashed lines</b>: time of arrival calculated from location'],
    ['text', ' '],

    ['text', '<b>x-zooming</b>: Mouse wheel'],
    ['text', '<b>y-zooming</b>: Mouse wheel + Shift'],
    ['text', '<b>x-panning</b>: Click and draw'],
]
