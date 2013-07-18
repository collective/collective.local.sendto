from setuptools import setup, find_packages
import os

version = '1.5.dev0'

setup(name='collective.local.sendto',
      version=version,
      description="Adds a 'Mailing' tab to selected content types that allows to select users that have a role on the content and send them a wysiwyg composed email. By Ecreall.",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from
      # http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        ],
      keywords='communication, auth',
      author='Thomas Desvenain',
      author_email='thomas.desvenain@gmail.com',
      url='http://svn.plone.org/svn/collective/',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['collective'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'collective.local.userlisting',
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-

      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
