"""Unit tests for processing CUES results from raw JSON to CSV

Run on command line with: python processresults_test.py
Should print 7 exceptions (these are expected output from ProcessResults)
and pass 8 tests.
"""

import datetime
import json
import processresults
import os
import unittest

class TestProcessResults(unittest.TestCase):
  
  def setUp(self):
    with open('processresults_test_input.json', 'r') as json_file:
      self.mock_results = json.load(json_file)
    
  def test_ProcessResults_creates_two_csv_files_with_expected_data(self):
    processresults.ProcessResults('processresults_test_input.json',
                                  'processresults_test_')

    metadata_headers = ('date_received,date_taken,participant_id,survey_type')
    with open('processresults_test_ssl-overridable-proceed.csv') as csv_file:
      csv_headers = csv_file.readline()
      self.assertIn(metadata_headers, csv_headers)
      self.assertIn(('"blah ""[CHOSEN]"" ""[ALTERNATIVE]."" blah",Q2,Q3,'
                     'To what degree do each of the following '
                     'adjectives describe this page?(A),'
                     'To what degree do each of the following '
                     'adjectives describe this page?(B),'
                     'To what degree do each of the following '
                     'adjectives describe this page?(C),Q7,URL'), csv_headers)
      
      test_line = csv_file.readline()
      self.assertIn('P2A1,P2A2,P2A3,P2AttributeAAnswer,'
                    'P2AttributeBAnswer,P2AttributeCAnswer,P2A7', test_line)
      test_line = csv_file.readline()
      self.assertIn('P3A1,P3A2,P3A3,P3AttributeAAnswer,'
                    'P3AttributeBAnswer,P3AttributeCAnswer,P3A7', test_line)

    with open('processresults_test_malware-noproceed.csv') as csv_file:
      csv_headers = csv_file.readline()
      self.assertIn(metadata_headers, csv_headers)
      self.assertIn(('"blah ""Back to safety"" ""blah"" blah",Q2,Q3,'
                     'To what degree do each of the following '
                     'adjectives describe this page?(A),'
                     'To what degree do each of the following '
                     'adjectives describe this page?(B),'
                     'To what degree do each of the following '
                     'adjectives describe this page?(C),Q7'), csv_headers)

      test_line = csv_file.readline()
      self.assertIn('P4A1,P4A2,P4A3,P4AttributeAAnswer,'
                    'P4AttributeBAnswer,P4AttributeCAnswer,P4A7', test_line)
              
  def test__DiscardResultsBeforeDate_filters_out_two_november_dates(self):
    results = self.mock_results
    results = processresults._DiscardResultsBeforeDate(
        results, datetime.datetime(2014, 12, 01, 0, 0, 0, 0))

    self.assertEqual(len(results), 3)
    self.assertEqual(results[0]['date_taken'], u'2015-01-05T11:48:39.760000')
    self.assertEqual(results[1]['date_taken'], u'2015-01-05T00:00:00.123456')
    self.assertEqual(results[2]['date_taken'], u'2015-01-05T01:02:03.123456')
    
  def test__FilterByCondition_filters_out_two_malware_noproceed(self):
    results = self.mock_results
    results = processresults._FilterByCondition('ssl-overridable-proceed',
                                                results)

    self.assertEqual(len(results), 3)
    self.assertEqual(results[0]['survey_type'], 'ssl-overridable-proceed.js')
    self.assertEqual(results[1]['survey_type'], 'ssl-overridable-proceed.js')
    self.assertEqual(results[2]['survey_type'], 'ssl-overridable-proceed.js')

  def test__CanonicalizeQuestions_filters_out_placeholder_questions(self):
    results = [r for r in self.mock_results
               if r['survey_type'] == 'malware-noproceed.js']
    processresults._CanonicalizeQuestions(results)

    self.assertEqual(len(results), 1)
    self.assertNotEqual(results[0]['responses'][0]['question'], 'PLACEHOLDER')
        
  def test__CanonicalizeQuestions_reorders_attribute_questions(self):
    results = [r for r in self.mock_results
               if r['survey_type'] == 'ssl-overridable-proceed.js']
    processresults._CanonicalizeQuestions(results)

    self.assertEqual(len(results), 3)
    for r in results:
      self.assertEqual(
          r['responses'][3]['question'],
          ('To what degree do each of the following adjectives '
          'describe this page?(A)'))
      self.assertEqual(
          r['responses'][4]['question'],
          ('To what degree do each of the following adjectives '
          'describe this page?(B)'))
      self.assertEqual(
          r['responses'][5]['question'],
          ('To what degree do each of the following adjectives '
          'describe this page?(C)'))            
    
  def test__CanonicalizeQuestions_replaces_urls_with_placeholder(self):
    results = [r for r in self.mock_results
               if r['survey_type'] == 'ssl-overridable-proceed.js']
    processresults._CanonicalizeQuestions(results)

    for r in results:
      self.assertEqual(
          r['responses'][0]['question'], 'blah "[CHOSEN]" "[ALTERNATIVE]." blah')
  
  def test__CanonicalizeQuestions_returns_canonical_index(self):
    results = [r for r in self.mock_results
               if r['survey_type'] == 'ssl-overridable-proceed.js']
    canonical_index = processresults._CanonicalizeQuestions(results)

    # 2nd item (index 1) in mock_results should be selected as canonical
    self.assertEqual(canonical_index, 1)
  
  def test__CanonicalizeQuestions_raises_exception_on_nonequal_questions(self):
    results = self.mock_results
    self.assertRaises(processresults.QuestionError,
                      processresults._CanonicalizeQuestions, results)

  def tearDown(self):
    try:
      os.remove('processresults_test_ssl-overridable-proceed.csv')
      os.remove('processresults_test_malware-noproceed.csv')
    except OSError:
      pass
        
if __name__ == '__main__':
  unittest.main()
