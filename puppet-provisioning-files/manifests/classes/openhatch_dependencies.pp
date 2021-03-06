# This Puppet class installs the OpenHatch codebase, its
# package dependencies, and runs 'buildout'.
class openhatch_dependencies {
  package { ['python2.6-dev', 'python-libxml2', 'memcached', 'python-mysqldb',
             'python-setuptools', 'libxml2-dev', 'libxslt1-dev', 'mysql-server',
             'mysql-client', 'python-xapian', 'python-imaging', 'subversion',
             'git-core']:
    ensure => installed,
  }
}

