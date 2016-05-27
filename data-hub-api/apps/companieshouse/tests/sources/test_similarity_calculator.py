from django.test.testcases import TestCase

from companieshouse.sources.similarity import SimilarityCalculator, clean_postcode, clean_name


class CleanPostcodeTestCase(TestCase):
    def test_empty(self):
        self.assertEqual(
            clean_postcode(''),
            ''
        )

    def test_None(self):
        self.assertEqual(
            clean_postcode(None),
            None
        )

    def test_correct(self):
        self.assertEqual(
            clean_postcode('SW1A 1AA'),
            'sw1a1aa'
        )

    def test_with_extra_spaces(self):
        self.assertEqual(
            clean_postcode(' SW1A    1 A A    '),
            'sw1a1aa'
        )


class CleanNameTestCase(TestCase):
    def test_empty(self):
        self.assertEqual(
            clean_name(''),
            ''
        )

    def test_None(self):
        self.assertEqual(
            clean_name(None),
            None
        )

    def test_correct(self):
        self.assertEqual(
            clean_name('My company'),
            'my company'
        )

    def test_with_common_parts_and_extra_spaces(self):
        self.assertEqual(
            clean_name('   The CompaNy.    lTd   '),
            'company'
        )


class SimilarityCalculatorTestCase(TestCase):
    def setUp(self):
        self.calc = SimilarityCalculator()

    def test_exact_names_and_exact_postcodes(self):
        """n1 = n2 AND p1 = p2 => 1"""
        self.calc.analyse_names('test', 'test')
        self.calc.analyse_postcodes('SW1A 1AA', 'sw1a1aa')
        self.assertEqual(self.calc.get_proximity(), 1)

    def test_similar_names_and_exact_postcodes(self):
        """n1 ~ n2 AND p1 = p2 => (>0.5)"""
        self.calc.analyse_names('another test', 'some test something')
        self.calc.analyse_postcodes('SW1A 1AA', 'sw1a1aa')
        self.assertEqual(self.calc.get_proximity(), 0.74)

    def test_different_names_and_exact_postcodes(self):
        """n1 != n2 AND p1 = p2 => (<0.5)"""
        self.calc.analyse_names('name1 part1', 'name2 part2')
        self.calc.analyse_postcodes('SW1A 1AA', 'sw1a1aa')
        self.assertEqual(self.calc.get_proximity(), 0.47)

    def test_exact_names_and_similar_postcodes(self):
        """n1 = n2 AND p1 ~ p2 => (>0.75)"""
        self.calc.analyse_names('test', 'test')
        self.calc.analyse_postcodes('SW1A 1AA', 'sw1a1ab')
        self.assertEqual(self.calc.get_proximity(), 0.76)

    def test_exact_names_and_different_postcodes(self):
        """n1 = n2 AND p1 != p2 => (>0.5)"""
        self.calc.analyse_names('test', 'test')
        self.calc.analyse_postcodes('SW1A 1AA', 'w1a5ab')
        self.assertEqual(self.calc.get_proximity(), 0.53)

    def test_similar_names_and_similar_postcodes(self):
        """n1 ~ n2 AND p1 ~ p2 => 0.5"""
        self.calc.analyse_names('another test', 'some test something')
        self.calc.analyse_postcodes('SW1A 1AA', 'sw1a5ab')
        self.assertEqual(self.calc.get_proximity(), 0.5)

    def test_similar_names_and_different_postcodes(self):
        """n1 ~ n2 AND p1 != p2 => (<0.5)"""
        self.calc.analyse_names('another test', 'some test something')
        self.calc.analyse_postcodes('SW1A 1AA', 'w1a5ab')
        self.assertEqual(self.calc.get_proximity(), 0.26)

    def test_different_names_and_similar_postcodes(self):
        """n1 != n2 AND p1 ~ p2 => (<0.5)"""
        self.calc.analyse_names('name1 part1', 'name2 part2')
        self.calc.analyse_postcodes('SW1A 1AA', 'sw1a1ab')
        self.assertEqual(self.calc.get_proximity(), 0.24)

    def test_different_names_and_different_postcodes(self):
        """n1 != n2 AND p1 != p2 => 0"""
        self.calc.analyse_names('name1 part1', 'part2 name2')
        self.calc.analyse_postcodes('SW1A 1AA', 'w1a5ab')
        self.assertEqual(self.calc.get_proximity(), 0)

    def test_with_extra_step(self):
        self.calc.analyse_names('test', 'test')
        self.calc.analyse_postcodes('SW1A 1AA', 'sw1a1aa')

        self.calc.analyse(
            'extra_prop',
            0.5,
            'string1', 'string2',
            lambda n1, n2: 1 if n1 == n2 else 0
        )
        self.assertEqual(self.calc.get_proximity(), 0.79)

    def test_raises_exception_names_not_analysed(self):
        self.calc.analyse_postcodes('SW1A 1AA', 'sw1a1aa')
        self.assertRaises(AssertionError, self.calc.get_proximity)

    def test_raises_exception_postcodes_not_analysed(self):
        self.calc.analyse_names('test', 'test')
        self.assertRaises(AssertionError, self.calc.get_proximity)
