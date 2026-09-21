"""Test the read-only completed-PDF bounds check without copying signed artwork."""
import unittest
from copy import deepcopy
from scripts.qa.check_txr1507_completed_placement import validate_measurements


def measurements():
    return {
        'associate_initials': {'x0': 328.23, 'x1': 342.72, 'top': 733.99, 'bottom': 744.53},
        'client_initials': {'x0': 409.53, 'x1': 424.02, 'top': 733.99, 'bottom': 744.53},
        'associate_signature': {'x0': 36.89, 'x1': 127.23, 'top': 514.17, 'bottom': 532.24},
        'client_signature': {'x0': 325.97, 'x1': 416.31, 'top': 514.17, 'bottom': 532.24},
        'associate_date': {'x0': 236.34, 'x1': 285.55, 'top': 523.54, 'bottom': 532.82},
        'client_date': {'x0': 525.42, 'x1': 574.63, 'top': 523.54, 'bottom': 532.82},
    }


class Txr1507CompletedMeasurementTests(unittest.TestCase):
    def test_observed_provider_bounds_fit_source_regions(self):
        self.assertTrue(validate_measurements(measurements()))

    def test_low_artwork_and_overwide_dates_are_not_accepted(self):
        for name, attribute, value in [('associate_signature', 'bottom', 553.5),
                                       ('client_signature', 'bottom', 554),
                                       ('client_date', 'x1', 580),
                                       ('associate_date', 'x1', 292),
                                       ('client_initials', 'bottom', 748),
                                       ('associate_initials', 'x0', 320)]:
            data = deepcopy(measurements())
            data[name][attribute] = value
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, name):
                validate_measurements(data)

    def test_missing_or_untested_fields_cannot_be_counted_as_verified(self):
        missing = measurements()
        del missing['client_signature']
        with self.assertRaises(ValueError):
            validate_measurements(missing)
        extra = measurements()
        extra['second_client_signature'] = extra['client_signature']
        with self.assertRaises(ValueError):
            validate_measurements(extra)


if __name__ == '__main__':
    unittest.main()
