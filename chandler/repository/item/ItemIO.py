
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from repository.item.Item import Item
from repository.util.SAX import XMLGenerator
from repository.util.ClassLoader import ClassLoader


class ItemWriter(object):

    def writeItem(self, item, version):

        status = item._status
        withSchema = (status & Item.CORESCHEMA) != 0
        kind = item.itsKind
        
        self._kind(kind)
        self._parent(item.itsParent, item._children is not None)
        self._name(item._name)

        itemClass = type(item)
        if withSchema or kind is None or kind.getItemClass() is not itemClass:
            self._className(itemClass.__module__, itemClass.__name__)
        else:
            self._className(None, None)

        if status & Item.DELETED == 0:
            isNew = (status & Item.NEW) != 0
            self._values(item, version, withSchema, isNew)
            self._references(item, version, withSchema, isNew)
            self._children(item, version, isNew)
            self._acls(item, version, isNew)

    def writeString(self, buffer, value):
        raise NotImplementedError, "%s.writeString" %(type(self))

    def writeSymbol(self, buffer, value):
        raise NotImplementedError, "%s.writeSymbol" %(type(self))

    def writeBoolean(self, buffer, value):
        raise NotImplementedError, "%s.writeBoolean" %(type(self))

    def writeInteger(self, buffer, value):
        raise NotImplementedError, "%s.writeInteger" %(type(self))

    def writeLong(self, buffer, value):
        raise NotImplementedError, "%s.writeLong" %(type(self))

    def writeFloat(self, buffer, value):
        raise NotImplementedError, "%s.writeFloat" %(type(self))

    def writeUUID(self, buffer, value):
        raise NotImplementedError, "%s.writeUUID" %(type(self))

    def writeList(self, buffer, item, value, withSchema, attrType):
        raise NotImplementedError, "%s.writeList" %(type(self))

    def writeDict(self, buffer, item, value, withSchema, attrType):
        raise NotImplementedError, "%s.writeDict" %(type(self))

    def writeStruct(self, buffer, item, value, withSchema, attrType):
        raise NotImplementedError, "%s.writeStruct" %(type(self))

    def _kind(self, kind):
        raise NotImplementedError, "%s._kind" %(type(self))

    def _parent(self, parent, isContainer):
        raise NotImplementedError, "%s._parent" %(type(self))

    def _name(self, name):
        raise NotImplementedError, "%s._name" %(type(self))

    def _className(self, moduleName, className):
        raise NotImplementedError, "%s._className" %(type(self))

    def _values(self, item, version, withSchema, isNew):
        raise NotImplementedError, "%s._values" %(type(self))

    def _references(self, item, version, withSchema, isNew):
        raise NotImplementedError, "%s._references" %(type(self))

    def _children(self, item, version, isNew):
        raise NotImplementedError, "%s._children" %(type(self))

    def _acls(self, item, version, isNew):
        raise NotImplementedError, "%s._acls" %(type(self))


class XMLItemWriter(ItemWriter):

    def __init__(self, generator):

        self.generator = generator

    def writeItem(self, item, version):

        attrs = {}
        attrs['uuid'] = item._uuid.str16()
        attrs['version'] = str(version)
        if (item._status & Item.CORESCHEMA) != 0:
            attrs['withSchema'] = 'True'

        self.generator.startElement('item', attrs)
        super(XMLItemWriter, self).writeItem(item, version)
        self.generator.endElement('item')

    def _name(self, name):

        if name is not None:
            self.generator.startElement('name', {})
            self.generator.characters(name)
            self.generator.endElement('name')
        
    def _kind(self, kind):

        if kind is not None:
            self.generator.startElement('kind', { 'type': 'path' })
            self.generator.characters(str(kind.itsPath))
            self.generator.endElement('kind')

    def _className(self, moduleName, className):

        if moduleName is not None and className is not None:
            self.generator.startElement('class', { 'module': moduleName })
            self.generator.characters(className)
            self.generator.endElement('class')
        
    def _parent(self, parent, isContainer):

        attrs = {}
        if isContainer:
            attrs['container'] = 'True'

        self.generator.startElement('parent', attrs)
        self.generator.characters(parent.itsUUID.str16())
        self.generator.endElement('parent')

    def _values(self, item, version, withSchema, isNew):
        item._values._xmlValues(self.generator, withSchema, version)

    def _references(self, item, version, withSchema, isNew):
        item._references._xmlValues(self.generator, withSchema, version)

    def _children(self, item, version, isNew):
        pass

    def _acls(self, item, version, isNew):
        pass


class ItemReader(object):

    def readItem(self, view, afterLoadHooks):
        raise NotImplementedError, "%s.readItem" %(type(self))

    def _kind(self, spec, withSchema, view, afterLoadHooks):
        return view._findSchema(spec, withSchema)

    def _parent(self, spec, withSchema, view, afterLoadHooks):
        return view.find(spec)

    def _class(self, moduleName, className, withSchema, kind,
               view, afterLoadHooks):

        if className is None:
            if kind is None:
                return Item
            else:
                return kind.getItemClass()
        else:
            return ClassLoader.loadClass(className, moduleName)

    def getUUID(self):
        raise NotImplementedError, "%s.getUUID" %(type(self))

    def getVersion(self):
        raise NotImplementedError, "%s.getVersion" %(type(self))

    def isDeleted(self):
        raise NotImplementedError, "%s.isDeleted" %(type(self))