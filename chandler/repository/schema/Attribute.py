
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from model.item.Item import Item
from model.item.ItemRef import RefDict
from model.schema.Kind import Kind


class Attribute(Item):

    def hasAspect(self, name):

        return self.hasAttributeValue(name)

    def getAspect(self, name, **kwds):

        if self.hasAttributeValue(name):
            return self.getAttributeValue(name)

        if self.hasAttributeValue('superAttribute'):
            return self.getAttributeValue('superAttribute').getAspect(name,
                                                                      **kwds)

        if self._kind is not None:
            aspectAttr = self._kind.getAttribute(name)
            if aspectAttr.hasAttributeValue('defaultValue'):
                return aspectAttr.getAttributeValue('defaultValue')
        
        return kwds.get('default', None)

    def _xmlRefs(self, generator, withSchema, mode):

        for attr in self._references.items():
            if self.getAttributeAspect(attr[0], 'persist', default=True):
                attr[1]._xmlValue(attr[0], self, generator, withSchema, mode)
