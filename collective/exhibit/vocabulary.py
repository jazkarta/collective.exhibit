from zope.schema.vocabulary import SimpleVocabulary
from zope.schema.vocabulary import SimpleTerm
from Products.CMFCore.utils import getToolByName


def primary_categories(context):
    """ See IVocabularyFactory interface
    """
    ctool = getToolByName(context, 'portal_catalog')
    if not ctool:
        return SimpleVocabulary([])

    primary = ctool.Indexes.get('getPrimaryCategory', None)
    if not primary:
        return SimpleVocabulary([])

    items = filter(None, primary.uniqueValues())
    items = sorted(items, key=str.lower)
    items = [SimpleTerm(i, i, i) for i in items]
    return SimpleVocabulary(items)

def secondary_categories(context):
    """ See IVocabularyFactory interface
    """
    ctool = getToolByName(context, 'portal_catalog')
    if not ctool:
        return SimpleVocabulary([])

    secondary = ctool.Indexes.get('getCategories', None)
    if not secondary:
        return SimpleVocabulary([])

    items = set(filter(None, secondary.uniqueValues()))

    primary = ctool.Indexes.get('getPrimaryCategory', None)
    if primary:
        primary_items = set(filter(None, primary.uniqueValues()))
        items = items - primary_items
    items = sorted(items, key=str.lower)
    items = [SimpleTerm(i, i, i) for i in items]
    return SimpleVocabulary(items)

