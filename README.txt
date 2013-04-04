Introduction
============

Provides a "Mailing" tab on selected content types.
It provides a 'send email' form where you can select recipients
from the list of members having a local role on the content.

Content types have just to implement ISendToAvailable,
or, if they are dexterity type, to enable the behaviour Send mail tab.

In your policy product :

  - Add 'collective.local.sendto' to the 'install_requires' parameter of setup.py

  - Add to the configure.zcml::

      <include package="collective.local.sendto" />
      <class class="my.package.content.MyContent.MyContent">
         <implements interface="collective.local.sendto.interfaces.ISendToAvailable" />
      </class>

Roles whose you can select users as recipients
are set by a site property : sendToRecipientRoles.

COMPATIBILITY
-------------

Plone 4.0, Plone 4.1
Wisywig behaviour needs Products.TinyMCE >= 1.0
