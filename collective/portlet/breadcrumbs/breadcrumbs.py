from ComputedAttribute import ComputedAttribute
from plone.app.portlets.browser import formhelper
from plone.app.portlets.portlets import base
from plone.app.uuid.utils import uuidToObject, uuidToCatalogBrain
from plone.app.vocabularies.catalog import CatalogSource
from plone.i18n.normalizer.interfaces import IIDNormalizer
from plone.memoize.instance import memoize
from plone.portlet.collection import PloneMessageFactory as _
from plone.portlets.interfaces import IPortletDataProvider
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zExceptions import NotFound
from zope import schema
from zope.component import getUtility
from zope.interface import implements
import random
import json
import os
import pkg_resources
from plone.app.layout.navigation.root import getNavigationRootObject
from zope.contentprovider.interfaces import IContentProvider
from plone.event.interfaces import IEvent
from zope.component import getMultiAdapter
from Acquisition import aq_inner
from Acquisition import aq_parent
from plone.app.layout.navigation.interfaces import INavigationRoot
from Products.CMFCore.interfaces._content import IFolderish
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from zope.i18n import translate
from plone.portlets.interfaces import IPortletAssignmentMapping
from Acquisition.interfaces import IAcquirer

from zope.i18nmessageid import MessageFactory
PMF = MessageFactory('plone')

class IBreadcrumbsPortlet(IPortletDataProvider):
    """A portlet which renders the results of a collection object.
    """

    header = schema.TextLine(
        title=_(u"Portlet header"),
        description=_(u"Title of the rendered portlet"),
        required=True)


class Assignment(base.Assignment):
    """
    Portlet assignment.
    This is what is actually managed through the portlets UI and associated
    with columns.
    """

    implements(IBreadcrumbsPortlet)

    header = u""

    def __init__(self, header=u""):
        self.header = header

    @property
    def title(self):
        """This property is used to give the title of the portlet in the
        "manage portlets" screen. Here, we use the title that the user gave.
        """
        return self.header


class Renderer(base.Renderer):

    _template = ViewPageTemplateFile('breadcrumbs.pt')
    render = _template

    def __init__(self, *args):
        base.Renderer.__init__(self, *args)

        self.portal_state = getMultiAdapter((self.context, self.request),
                                            name=u'plone_portal_state')
        self.is_rtl = self.portal_state.is_rtl()

        breadcrumbs_view = getMultiAdapter((self.context, self.request),
                                           name='breadcrumbs_view')
        
        self.navigation_root_url = self.portal_state.navigation_root_url()
        self.breadcrumbs = breadcrumbs_view.breadcrumbs()

        self.assignment_context = self.get_assignment_context()
        
    
    def get_assignment_context(self):
        # this is odd... should be much more straightforward?
        # also, this is pretty slow.
        manager = self.manager
        context = self.context
        assignment = self.data

        allAss = []
        while not assignment in allAss:
            pam = getMultiAdapter((context, manager), IPortletAssignmentMapping)
            allAss = pam.values()
            if assignment in allAss:
                break

            if IAcquirer.providedBy(context):
                context = aq_parent(aq_inner(context))
            else:
                context = context.__parent__

        return context

    def assignment_context_url(self):
        return self.assignment_context.absolute_url()


    def css_class(self):
        header = self.data.header
        normalizer = getUtility(IIDNormalizer)
        return "portlet-breadcrumbs-%s" % normalizer.normalize(header)



class AddForm(base.AddForm):

    schema = IBreadcrumbsPortlet
    label = _(u"Add Breadcrumbs Portlet")
    description = _(u"This portlet renders the Plone Breadcrumbs in context")

    def create(self, data):
        return Assignment(**data)


class EditForm(base.EditForm):
    schema = IBreadcrumbsPortlet
    label = _(u"Edit Breadcrumbs Portlet")
    description = _(u"This portlet renders the Plone Breadcrumbs in context")

