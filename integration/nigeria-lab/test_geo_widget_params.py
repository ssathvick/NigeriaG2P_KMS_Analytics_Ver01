import unittest
from fix_geo_widget_params import update_widgets

class GeoWidgetMetadataTests(unittest.TestCase):
    def test_updates_geo_and_preserves_configuration(self):
        data={'panels':[{'widgets':[{'widget-data-source':{'type':'api','service':'master-data','endpoint':'geo-level-values','level_id':'State / FCT','params':{'page_size':50}}},{'widget-data-source':{'type':'api','service':'other','endpoint':'geo-level-values','level_id':'unchanged'}}]}]}
        self.assertEqual(update_widgets(data),1)
        source=data['panels'][0]['widgets'][0]['widget-data-source']
        self.assertEqual(source['params'],{'page_size':50,'level_id':'State / FCT'})
        self.assertEqual((source['valueKey'],source['labelKey']),('level_value_id','level_value_mnemonic'))
        self.assertEqual(update_widgets(data),0)
        self.assertNotIn('params',data['panels'][0]['widgets'][1]['widget-data-source'])

    def test_rejects_unexpected_params(self):
        with self.assertRaises(ValueError):
            update_widgets({'widget-data-source':{'type':'api','service':'master-data','endpoint':'geo-level-values','level_id':'state','params':'invalid'}})

if __name__=='__main__': unittest.main()
