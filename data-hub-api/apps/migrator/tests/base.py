import datetime
from unittest import mock

from django.utils import timezone
from django.test.testcases import TransactionTestCase

from reversion.models import Revision, Version

from migrator.query import REVISION_COMMENT_CDMS_REFRESH

from cdms_api.tests.rest.utils import mocked_cdms_get, mocked_cdms_create, mocked_cdms_update


class BaseMockedCDMSRestApiTestCase(TransactionTestCase):
    @mock.patch('migrator.query.rest_connection')
    def __call__(self, result, mocked_cdms_api, *args, **kwargs):
        # mocking the modified value so that the tests don't depend on the automatic 'now' datetime value
        # and therefore we can catch all hidden problems.
        self.mocked_modified = (timezone.now() + datetime.timedelta(minutes=1)).replace(microsecond=0)

        mocked_cdms_api.create.side_effect = mocked_cdms_create()
        mocked_cdms_api.get.side_effect = mocked_cdms_get(get_data={
            'ModifiedOn': self.mocked_modified
        })
        mocked_cdms_api.update.side_effect = mocked_cdms_update()

        self.mocked_cdms_api = mocked_cdms_api
        super(BaseMockedCDMSRestApiTestCase, self).__call__(result, *args, **kwargs)

    def adjust_modified_field(self, obj, modified):
        """
        Sets the obj.modified to 'modified' without calling cdms.
        """
        obj.__class__.objects.skip_cdms().filter(pk=obj.pk).update(modified=modified)
        obj.modified = modified

    def assertAPICalled(self, model, verb, kwargs, tot=1):
        if tot == 1:
            kwargs = [kwargs]

        for index, single_kwargs in enumerate(kwargs):
            mock_verb = getattr(self.mocked_cdms_api, verb)

            self.assertEqual(mock_verb.call_count, tot)

            _args, _kwargs = mock_verb.call_args_list[index]
            self.assertEqual(_args, (model.cdms_migrator.service,))
            self.assertEqual(set(_kwargs.keys()), set(single_kwargs.keys()))

            for key, value in _kwargs.items():
                single_value = single_kwargs[key]
                if isinstance(value, list):
                    value = sorted(value)
                    single_value = sorted(single_value)
                self.assertEqual(value, single_value)

    def assertAPINotCalled(self, verbs):
        if not isinstance(verbs, list):
            verbs = [verbs]

        for verb in verbs:
            mock_verb = getattr(self.mocked_cdms_api, verb)
            self.assertEqual(
                mock_verb.call_count, 0,
                '%s should not get called' % verb
            )

    def assertNoAPICalled(self):
        self.assertAPINotCalled(['create', 'list', 'update', 'delete', 'get'])

    def assertAPICreateCalled(self, model, kwargs, tot=1):
        self.assertAPICalled(model, 'create', kwargs=kwargs, tot=tot)

    def assertAPIUpdateCalled(self, model, kwargs, tot=1):
        self.assertAPICalled(model, 'update', kwargs=kwargs, tot=tot)

    def assertAPIGetCalled(self, model, kwargs, tot=1):
        self.assertAPICalled(model, 'get', kwargs=kwargs, tot=tot)

    def assertAPIListCalled(self, model, kwargs, tot=1):
        # 'ModifiedOn asc' is the default ordering so just add it to kwargs if not present
        if 'order_by' not in kwargs:
            kwargs['order_by'] = ['ModifiedOn asc']
        self.assertAPICalled(model, 'list', kwargs=kwargs, tot=tot)

    def assertAPIDeleteCalled(self, model, kwargs, tot=1):
        self.assertAPICalled(model, 'delete', kwargs=kwargs, tot=tot)

    def assertNoRevisions(self):
        self.assertEqual(Version.objects.count(), 0)
        self.assertEqual(Revision.objects.count(), 0)

    def assertIsCDMSRefreshRevision(self, revision):
        self.assertEqual(revision.comment, REVISION_COMMENT_CDMS_REFRESH)

    def assertIsNotCDMSRefreshRevision(self, revision):
        self.assertNotEqual(revision.comment, REVISION_COMMENT_CDMS_REFRESH)

    def reset_revisions(self):
        Version.objects.all().delete()
        Revision.objects.all().delete()

        self.assertNoRevisions()
