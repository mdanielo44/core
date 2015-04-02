# -*- coding: utf-8 -*-
'''
Created on 11 fevr. 2015

@author: sd-libre
'''

from __future__ import unicode_literals
from lucterios.framework.test import LucteriosTest
from lucterios.framework.xfergraphic import XferContainerAcknowledge, XFER_DBOX_WARNING, \
    XferContainerCustom
from django.utils.http import urlquote_plus
from lucterios.framework.tools import StubAction
from lucterios.CORE.models import Parameter
from lucterios.CORE.parameters import Params
from lucterios.CORE.views import ParamSave
from django.utils import six

class GenericTest(LucteriosTest):
    # pylint: disable=too-many-public-methods

    def __init__(self, methodName):
        LucteriosTest.__init__(self, methodName)
        self.xfer = None

    def setUp(self):
        self.xfer_class = XferContainerAcknowledge
        self.xfer_class.is_view_right = ''
        LucteriosTest.setUp(self)
        self.value = False
        self.xfer = XferContainerCustom()
        Params.clear()

    def callparam(self):
        self.factory.xfer = self.xfer
        self.call("CORE/params", {}, False)

    def test_help(self):
        response = self.client.get('/Help', {})
        self.assertEqual(response.status_code, 200, "HTTP error:" + str(response.status_code))  # pylint: disable=E1101
        help_content = six.text_type(response.content)  # pylint: disable=E1101
        self.assertGreaterEqual(help_content.find('<html>'), 17)
        self.assertLessEqual(help_content.find('<html>'), 21)

        response = self.client.get('/Help', {'helpid':'lucterios.CORE-01_password.html'})
        self.assertEqual(response.status_code, 200, "HTTP error:" + str(response.status_code))  # pylint: disable=E1101
        help_content = six.text_type(response.content)  # pylint: disable=E1101
        self.assertGreaterEqual(help_content.find('<h1>'), 1)
        self.assertLessEqual(help_content.find('<h1>'), 4)

    def test_simple(self):
        self.call('/customer/details', {'id':12, 'value':'abc'}, False)
        self.assert_observer('Core.Acknowledge', 'customer', 'details')
        self.assert_count_equal('CONTEXT', 1)
        self.assert_count_equal('CONTEXT/PARAM', 2)
        self.assert_xml_equal('CONTEXT/PARAM[@name="id"]', '12')
        self.assert_xml_equal('CONTEXT/PARAM[@name="value"]', 'abc')
        self.assert_count_equal('CLOSE_ACTION', 0)

    def test_close(self):
        def fillresponse_close():
            self.factory.xfer.set_close_action(StubAction("close", "", "customer", "list"))
        self.factory.xfer.fillresponse = fillresponse_close
        self.call('/customer/details', {}, False)
        self.assert_observer('Core.Acknowledge', 'customer', 'details')
        self.assert_count_equal('CONTEXT', 0)
        self.assert_count_equal('ACTION', 0)
        self.assert_count_equal('CLOSE_ACTION/ACTION', 1)
        self.assert_action_equal('CLOSE_ACTION/ACTION', ("close", None, "customer", "list", 1, 1, 1))

    def test_redirect(self):
        def fillresponse_redirect():
            self.factory.xfer.redirect_action(StubAction("redirect", "", "customer", "list"))
        self.factory.xfer.fillresponse = fillresponse_redirect
        self.call('/customer/details', {}, False)
        self.assert_observer('Core.Acknowledge', 'customer', 'details')
        self.assert_count_equal('CONTEXT', 0)
        self.assert_count_equal('ACTION', 1)
        self.assert_action_equal('ACTION', ("redirect", None, "customer", "list", 1, 1, 1))

    def test_confirme(self):
        self.value = False
        def fillresponse_confirme():
            if self.factory.xfer.confirme("Do you want?"):
                self.value = True
        self.factory.xfer.fillresponse = fillresponse_confirme
        self.call('/customer/details', {}, False)
        self.assertEqual(self.value, False)
        self.assert_observer('Core.DialogBox', 'customer', 'details')
        self.assert_count_equal('CONTEXT', 0)
        self.assert_attrib_equal('TEXT', 'type', '2')
        self.assert_xml_equal('TEXT', 'Do you want?')
        self.assert_count_equal('ACTIONS/ACTION', 2)
        self.assert_action_equal('ACTIONS/ACTION[1]', ('Oui', 'images/ok.png', 'customer', 'details', 1, 1, 1, {'CONFIRME':"YES"}))
        self.assert_action_equal('ACTIONS/ACTION[2]', ('Non', 'images/cancel.png'))

        self.call('/customer/details', {'CONFIRME':'YES'}, False)
        self.assertEqual(self.value, True)
        self.assert_attrib_equal('', 'observer', 'Core.Acknowledge')

    def test_message(self):
        def fillresponse_message():
            self.factory.xfer.message("Finished!", XFER_DBOX_WARNING)
        self.factory.xfer.fillresponse = fillresponse_message
        self.call('/customer/details', {}, False)
        self.assert_observer('Core.DialogBox', 'customer', 'details')
        self.assert_count_equal('CONTEXT', 0)
        self.assert_attrib_equal('TEXT', 'type', '3')
        self.assert_xml_equal('TEXT', 'Finished!')
        self.assert_count_equal('ACTIONS/ACTION', 1)
        self.assert_action_equal('ACTIONS/ACTION', ('Ok', 'images/ok.png'))

    def test_traitment(self):
        self.value = False
        def fillresponse_traitment():
            if self.factory.xfer.traitment("customer/images/foo.png", "Traitment{[br/]}Wait...", "Done"):
                self.value = True
        self.factory.xfer.fillresponse = fillresponse_traitment
        self.call('/customer/details', {}, False)
        self.assertEqual(self.value, False)
        self.assert_observer('Core.Custom', 'customer', 'details')
        self.assert_count_equal('CONTEXT', 0)
        self.assert_count_equal('COMPONENTS/*', 3)
        self.assert_xml_equal('COMPONENTS/LABELFORM[@name="info"]', '{[br/]}{[center]}Traitment{[br/]}Wait...{[/center]}')
        self.assert_xml_equal('COMPONENTS/IMAGE[@name="img_title"]', 'customer/images/foo.png')
        self.assert_action_equal('COMPONENTS/BUTTON[@name="Next"]/ACTIONS/ACTION', ('Traitement...', None, 'customer', 'details', 1, 1, 1, {'RELOAD':"YES"}))
        self.assert_xml_equal('COMPONENTS/BUTTON[@name="Next"]/JavaScript', urlquote_plus('parent.refresh()'))
        self.assert_count_equal('ACTIONS/ACTION', 1)
        self.assert_action_equal('ACTIONS/ACTION', ('Annuler', 'images/cancel.png'))

        self.call('/customer/details', {'RELOAD':'YES'}, False)
        self.assertEqual(self.value, True)
        self.assert_observer('Core.Custom', 'customer', 'details')
        self.assert_count_equal('CONTEXT', 1)
        self.assert_attrib_equal('CONTEXT/PARAM', 'name', 'RELOAD')
        self.assert_xml_equal('CONTEXT/PARAM', 'YES')
        self.assert_count_equal('COMPONENTS/*', 2)
        self.assert_xml_equal('COMPONENTS/IMAGE[@name="img_title"]', 'customer/images/foo.png')
        self.assert_xml_equal('COMPONENTS/LABELFORM[@name="info"]', '{[br/]}{[center]}Done{[/center]}')
        self.assert_action_equal('ACTIONS/ACTION', ('Fermer', 'images/close.png'))

    def test_parameters_text(self):
        param = Parameter.objects.create(name='param_text', typeparam=0)  # pylint: disable=no-member
        param.args = "{'Multi':False}"
        param.value = 'my value'
        param.save()
        Params.fill(self.xfer, ['param_text'], 1, 1, True)
        Params.fill(self.xfer, ['param_text'], 1, 2, False)
        self.callparam()
        self.assert_count_equal('COMPONENTS/*', 4)
        self.assert_count_equal('COMPONENTS/LABELFORM[@name="lbl_param_text"]', 2)
        self.assert_xml_equal('COMPONENTS/LABELFORM[@name="param_text"]', 'my value')
        self.assert_xml_equal('COMPONENTS/EDIT[@name="param_text"]', 'my value')

        self.factory.xfer = ParamSave()
        self.call('/CORE/paramSave', {'params':'param_text', 'param_text':'new value'}, False)
        self.assert_observer('Core.Acknowledge', 'CORE', 'paramSave')
        self.assertEqual(Params.getvalue('param_text'), 'new value')

    def test_parameters_memo(self):
        param = Parameter.objects.create(name='param_memo', typeparam=0)  # pylint: disable=no-member
        param.args = "{'Multi':True}"
        param.value = 'other value'
        param.save()
        Params.fill(self.xfer, ['param_memo'], 1, 1, True)
        Params.fill(self.xfer, ['param_memo'], 1, 2, False)
        self.callparam()
        self.assert_count_equal('COMPONENTS/*', 4)
        self.assert_count_equal('COMPONENTS/LABELFORM[@name="lbl_param_memo"]', 2)
        self.assert_xml_equal('COMPONENTS/LABELFORM[@name="param_memo"]', 'other value')
        self.assert_xml_equal('COMPONENTS/MEMO[@name="param_memo"]', 'other value')

        self.factory.xfer = ParamSave()
        self.call('/CORE/paramSave', {'params':'param_memo', 'param_memo':'new special value'}, False)
        self.assert_observer('Core.Acknowledge', 'CORE', 'paramSave')
        self.assertEqual(Params.getvalue('param_memo'), 'new special value')

    def test_parameters_int(self):
        param = Parameter.objects.create(name='param_int', typeparam=1)  # pylint: disable=no-member
        param.args = "{'Min':5, 'Max':25}"
        param.value = '5'
        param.save()
        Params.fill(self.xfer, ['param_int'], 1, 1, True)
        Params.fill(self.xfer, ['param_int'], 1, 2, False)
        self.callparam()
        self.assert_count_equal('COMPONENTS/*', 4)
        self.assert_count_equal('COMPONENTS/LABELFORM[@name="lbl_param_int"]', 2)
        self.assert_xml_equal('COMPONENTS/LABELFORM[@name="param_int"]', '5')
        self.assert_xml_equal('COMPONENTS/FLOAT[@name="param_int"]', '5')

        self.assert_attrib_equal('COMPONENTS/FLOAT[@name="param_int"]', 'min', '5.0')
        self.assert_attrib_equal('COMPONENTS/FLOAT[@name="param_int"]', 'max', '25.0')
        self.assert_attrib_equal('COMPONENTS/FLOAT[@name="param_int"]', 'prec', '0')

        self.factory.xfer = ParamSave()
        self.call('/CORE/paramSave', {'params':'param_int', 'param_int':'13'}, False)
        self.assert_observer('Core.Acknowledge', 'CORE', 'paramSave')
        self.assertEqual(Params.getvalue('param_int'), 13)

    def test_parameters_float(self):
        param = Parameter.objects.create(name='param_float', typeparam=2)  # pylint: disable=no-member
        param.args = "{'Min':20, 'Max':30, 'Prec':2}"
        param.value = '22.25'
        param.save()
        Params.fill(self.xfer, ['param_float'], 1, 1, True)
        Params.fill(self.xfer, ['param_float'], 1, 2, False)
        self.callparam()
        self.assert_count_equal('COMPONENTS/*', 4)
        self.assert_count_equal('COMPONENTS/LABELFORM[@name="lbl_param_float"]', 2)
        self.assert_xml_equal('COMPONENTS/LABELFORM[@name="param_float"]', '22.25')
        self.assert_xml_equal('COMPONENTS/FLOAT[@name="param_float"]', '22.25')
        self.assert_attrib_equal('COMPONENTS/FLOAT[@name="param_float"]', 'min', '20.0')
        self.assert_attrib_equal('COMPONENTS/FLOAT[@name="param_float"]', 'max', '30.0')
        self.assert_attrib_equal('COMPONENTS/FLOAT[@name="param_float"]', 'prec', '2')

        self.factory.xfer = ParamSave()
        self.call('/CORE/paramSave', {'params':'param_float', 'param_float':'26.87'}, False)
        self.assert_observer('Core.Acknowledge', 'CORE', 'paramSave')
        self.assertEqual(Params.getvalue('param_float'), 26.87)

    def test_parameters_bool(self):
        param = Parameter.objects.create(name='param_bool', typeparam=3)  # pylint: disable=no-member
        param.args = "{}"
        param.value = 'False'
        param.save()
        Params.fill(self.xfer, ['param_bool'], 1, 1, True)
        Params.fill(self.xfer, ['param_bool'], 1, 2, False)
        self.callparam()
        self.assert_count_equal('COMPONENTS/*', 4)
        self.assert_count_equal('COMPONENTS/LABELFORM[@name="lbl_param_bool"]', 2)
        self.assert_xml_equal('COMPONENTS/LABELFORM[@name="param_bool"]', 'Non')
        self.assert_xml_equal('COMPONENTS/CHECK[@name="param_bool"]', '0')

        self.factory.xfer = ParamSave()
        self.call('/CORE/paramSave', {'params':'param_bool', 'param_bool':'1'}, False)
        self.assert_observer('Core.Acknowledge', 'CORE', 'paramSave')
        self.assertEqual(Params.getvalue('param_bool'), True)

    def test_parameters_select(self):
        param = Parameter.objects.create(name='param_select', typeparam=4)  # pylint: disable=no-member
        param.args = "{'Enum':4}"
        param.value = '2'
        param.save()
        Params.fill(self.xfer, ['param_select'], 1, 1, True)
        Params.fill(self.xfer, ['param_select'], 1, 2, False)
        self.callparam()
        self.assert_count_equal('COMPONENTS/*', 4)
        self.assert_count_equal('COMPONENTS/LABELFORM[@name="lbl_param_select"]', 2)
        self.assert_xml_equal('COMPONENTS/LABELFORM[@name="param_select"]', 'param_select.2')
        self.assert_xml_equal('COMPONENTS/SELECT[@name="param_select"]', '2')
        self.assert_count_equal('COMPONENTS/SELECT[@name="param_select"]/CASE', 4)

        self.factory.xfer = ParamSave()
        self.call('/CORE/paramSave', {'params':'param_select', 'param_select':'1'}, False)
        self.assert_observer('Core.Acknowledge', 'CORE', 'paramSave')
        self.assertEqual(Params.getvalue('param_select'), 1)
