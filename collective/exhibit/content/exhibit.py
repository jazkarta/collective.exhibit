"""Definition of the Exhibit content type
"""

from zope.interface import implements
from plone.memoize import volatile
from AccessControl import ClassSecurityInfo

from Products.CMFCore.CMFCatalogAware import CMFCatalogAware
from Products.CMFCore.permissions import View
from Products.Archetypes import atapi
from Products.ATContentTypes.content import folder
from Products.ATContentTypes.content import schemata
from archetypes.referencebrowserwidget import ReferenceBrowserWidget

from collective.exhibit import contenttypesMessageFactory as _

from collective.exhibit.interfaces import IExhibit
from collective.exhibit.config import PROJECTNAME


ExhibitSchema = folder.ATFolderSchema.copy() + atapi.Schema((

    atapi.TextField(
        'text',
        searchable=True,
        default_content_type='text/html',
        allowable_content_types=('text/html','text/plain'),
        default_output_type='text/x-html-safe',
        widget=atapi.RichWidget(
            label=_(u"Exhibit Text"),
            description=_(u"Text for exhibit home page"),
            rows=20,
            allow_file_upload=False,
        ),
        required=False,
    ),
))

schemata.finalizeATCTSchema(
    ExhibitSchema,
    folderish=True,
    moveDiscussion=False
)


class Exhibit(folder.ATFolder):
    """Exhibit"""
    implements(IExhibit)
    security = ClassSecurityInfo()

    meta_type = "Exhibit"
    schema = ExhibitSchema

atapi.registerType(Exhibit, PROJECTNAME)
