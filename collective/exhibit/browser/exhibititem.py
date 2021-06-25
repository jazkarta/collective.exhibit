from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from AccessControl.SecurityManagement import getSecurityManager
from AccessControl.PermissionRole import rolesForPermissionOn
from Products.statusmessages.interfaces import IStatusMessage

from collective.exhibit import exhibitMessageFactory as _


class View(BrowserView):
    """A view providing a permission check"""
    __call__ = ViewPageTemplateFile("exhibititem_templates/view.pt")

    def update(self):
        super(View, self).update()

        # Determine if the referenced object is viewable by anonymous.
        sm = getSecurityManager()
        try:
            referenced = self.context._get_referenced()
        except AttributeError:
            referenced = None
        if (referenced is not None and
              sm.checkPermission('Modify portal content', self.context)):
            view_this = 'Anonymous' in rolesForPermissionOn('View',
                                                            self.context)
            view_ref = 'Anonymous' in rolesForPermissionOn('View', referenced)
            # If the current user is an editor, and the exhibit item
            # item is visible to anonymous users, but the referenced
            # item is not, show a warning:
            if view_this and not view_ref:
                IStatusMessage(self.request).add(_('The referenced item is '
                                                   'not published, so this '
                                                   'exhibit item will not be '
                                                   'visible to anonymous '
                                                   'users.'),
                                                 'warning')
