import h5py


class DataPaths:
    TITLE = [
        'raw_data_1/title'
    ]

    RUN_NUMBER = [
        'raw_data_1/run_number'
    ]

    SAMPLE_NAME = [
        'raw_data_1/sample/name'
    ]

    AREA = [
        'raw_data_1/beamline'
    ]

    LAB = [
        'raw_data_1/instrument/source/name'
    ]

    RESOLUTION = [
        'raw_data_1/selog/pulse_width/value'
    ]

    TEMPERATURE = [
        'raw_data_1/sample/temperature',
        'raw_data_1/selog/Temp_Sample/value'
    ]

    FIELD = [
        'raw_data_1/sample/magnetic_field',
        'raw_data_1/selog/Field_ZF_Magnitude/value'
    ]

    HISTOGRAMS = [
        'raw_data_1/detector_1/counts'
    ]


class Attributes:
    UNITS = [
        'units'
    ]

    FIRST_GOOD_BIN = [
        'first_good_bin'
    ]

    LAST_GOOD_BIN = [
        'last_good_bin'
    ]

    T0_BIN = [
        't0_bin'
    ]


def get_value(data_paths, hdf_file_object, full=None):
    for path in data_paths:
        if path in hdf_file_object:
            if full:
                return hdf_file_object[path]
            return hdf_file_object[path][0]
        elif path == data_paths[-1]:
            raise KeyError("Path not found in HDF file.")


def get_attribute(data_paths, attribute, hdf_file_object):
    dataset = get_value(data_paths, hdf_file_object, True)

    for att in attribute:
        if att in dataset.attrs:
            return dataset.attrs[att]
        elif att == attribute[-1]:
            raise AttributeError("Attribute not found on dataset.")


def get_meta_values(path):
    f = h5py.File(path, 'r+')

    title = get_value(DataPaths.TITLE, f)
    run_number = get_value(DataPaths.RUN_NUMBER, f)
    sample = get_value(DataPaths.SAMPLE_NAME, f)
    lab = get_value(DataPaths.LAB, f)
    area = get_value(DataPaths.AREA, f)
    resolution = get_value(DataPaths.RESOLUTION, f)
    resolution_units = get_attribute(DataPaths.RESOLUTION, Attributes.UNITS, f)
    temperature = get_value(DataPaths.TEMPERATURE, f)
    temperature_units = get_attribute(DataPaths.TEMPERATURE, Attributes.UNITS, f)
    field = get_value(DataPaths.FIELD, f)
    field_units = get_attribute(DataPaths.FIELD, Attributes.UNITS, f)

    first_good_bin = get_attribute(DataPaths.HISTOGRAMS, Attributes.FIRST_GOOD_BIN, f)
    last_good_bin = get_attribute(DataPaths.HISTOGRAMS, Attributes.LAST_GOOD_BIN, f)
    t0_bin = get_attribute(DataPaths.HISTOGRAMS, Attributes.T0_BIN, f)


def get_histograms(path):
    f = h5py.File(path, 'r+')

    data = get_value(DataPaths.HISTOGRAMS, f, True)


file = r"C:\Users\Alec\Downloads\MUSR00073926.nxs_v2"
file2 = r"C:\Users\Alec\BEAMS\test\MUSR00071470.nxs_v2"
file3 = r"C:\Users\Alec\BEAMS\test\MUSR00073926.nxs_v2"
file4 = r"C:\Users\Alec\BEAMS\test\MUSR00076331.nxs_v2"
file5 = r"C:\Users\Alec\BEAMS\test\MUSR00078210.nxs_v2"
file6 = r"C:\Users\Alec\BEAMS\test\MUSR00081427.nxs_v2"
file7 = r"C:\Users\Alec\BEAMS\test\MUSR00082432.nxs_v2"
file8 = r"C:\Users\Alec\BEAMS\test\MUSR00084776.nxs_v2"
file9 = r"C:\Users\Alec\BEAMS\test\MUSR00084882.nxs_v2"
file10 = r"C:\Users\Alec\BEAMS\test\MUSR00083581.nxs"


def check_keys_and_attrs(current_path, look_for):
    h50 = f[current_path]
    try:
        for key in h50.keys():
            if look_for.lower() in current_path.lower() or look_for.lower() in key.lower():
                print(current_path, key, get_value(current_path + '/{}'.format(key), f))
            check_keys_and_attrs(current_path + '/{}'.format(key), look_for)
    except AttributeError:
        for att in h50.attrs:
            if look_for.lower() in current_path.lower() or look_for.lower() in att.lower():
                print(current_path, att, h50.attrs[att])


# check_keys_and_attrs('raw_data_1', 'date')
#
# print(get_single_value('raw_data_1/periods/good_frames', f))
# print(get_single_attribute('raw_data_1/runlog/good_frames/time', 'start', f))


