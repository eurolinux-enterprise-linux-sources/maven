%global debug_package %{nil}

Name:           maven
Version:        3.0.5
Release:        17%{?dist}
Summary:        Java project management and project comprehension tool

Group:          Development/Tools
License:        ASL 2.0
URL:            http://maven.apache.org/
Source0:        http://archive.apache.org/dist/%{name}/%{name}-3/%{version}/source/apache-%{name}-%{version}-src.tar.gz
Source1:        maven-bash-completion
Source2:        mvn.1

# 2xx for created non-buildable sources
Source200:      %{name}-script

# Patch1XX could be upstreamed probably
Patch100:       0005-Use-generics-in-modello-generated-code.patch

# Patch2XX backported from upstream
# Fixes MNG-5402 (patch from upstream commit f95ab2e)
Patch200:       0001-MNG-5402-Better-build-number-for-git.patch

# Access Maven Central via HTTPS by default
Patch300:       0001-default-to-ssl-for-central.patch

BuildArch:      noarch

BuildRequires:  maven-local
BuildRequires:  xmvn >= 1.3.0-5

BuildRequires:  aether-api >= 1.13.1-8
BuildRequires:  aether-connector-wagon
BuildRequires:  aether-impl
BuildRequires:  aether-spi
BuildRequires:  aether-util
BuildRequires:  aopalliance
BuildRequires:  apache-commons-cli
BuildRequires:  apache-commons-jxpath
BuildRequires:  apache-resource-bundles
BuildRequires:  atinject
BuildRequires:  cglib
BuildRequires:  easymock
BuildRequires:  google-guice >= 3.1.3-8
BuildRequires:  hamcrest
BuildRequires:  junit
BuildRequires:  maven-assembly-plugin
BuildRequires:  maven-compiler-plugin
BuildRequires:  maven-install-plugin
BuildRequires:  maven-jar-plugin
BuildRequires:  maven-javadoc-plugin
BuildRequires:  maven-parent
BuildRequires:  maven-remote-resources-plugin
BuildRequires:  maven-resources-plugin
BuildRequires:  maven-site-plugin
BuildRequires:  maven-surefire-plugin
BuildRequires:  maven-surefire-provider-junit4
BuildRequires:  maven-wagon
BuildRequires:  objectweb-asm
BuildRequires:  plexus-cipher
BuildRequires:  plexus-classworlds
BuildRequires:  plexus-containers-component-annotations
BuildRequires:  plexus-containers-component-metadata >= 1.5.5
BuildRequires:  plexus-containers-container-default
BuildRequires:  plexus-interpolation
BuildRequires:  plexus-sec-dispatcher
BuildRequires:  plexus-utils
BuildRequires:  sisu-inject-bean
BuildRequires:  sisu-inject-plexus
BuildRequires:  slf4j
BuildRequires:  xmlunit
%if 0%{?fedora}
BuildRequires:  animal-sniffer >= 1.6-5
%endif

# Theoretically Maven might be usable with just JRE, but typical Maven
# workflow requires full JDK, wso we require it here.
Requires:       java-devel

# XMvn does generate auto-requires, but explicit requires are still
# needed because some symlinked JARs are not present in Maven POMs or
# their dependency scope prevents them from being added automatically
# by XMvn.  It would be possible to explicitly specify only
# dependencies which are not generated automatically, but adding
# everything seems to be easier.
Requires:       aether-api
Requires:       aether-connector-wagon
Requires:       aether-impl
Requires:       aether-spi
Requires:       aether-util
Requires:       aopalliance
Requires:       apache-commons-cli
Requires:       apache-commons-codec
Requires:       apache-commons-logging
Requires:       atinject
Requires:       cglib
Requires:       google-guice
Requires:       guava
Requires:       httpcomponents-client
Requires:       httpcomponents-core
Requires:       maven-wagon
Requires:       objectweb-asm
Requires:       plexus-cipher
Requires:       plexus-containers-component-annotations
Requires:       plexus-interpolation
Requires:       plexus-sec-dispatcher
Requires:       plexus-utils
Requires:       sisu-inject-bean
Requires:       sisu-inject-plexus

# for noarch->arch change
Obsoletes:      %{name} < 0:%{version}-%{release}

# maven2 bin package no longer exists.
Obsoletes:      maven2 < 2.2.1-99
Provides:       maven2 = %{version}-%{release}

%description
Maven is a software project management and comprehension tool. Based on the
concept of a project object model (POM), Maven can manage a project's build,
reporting and documentation from a central piece of information.

%package        javadoc
Summary:        API documentation for %{name}
Group:          Documentation

%description    javadoc
%{summary}.

%prep
%setup -q -n apache-%{name}-%{version}%{?ver_add}
%patch100 -p1
%patch200 -p1
%patch300 -p1

# Generate build number based on package release number
%pom_remove_plugin :buildnumber-maven-plugin maven-core
sed -i "
/buildNumber=/ {
  s/=.*/=Red Hat %{version}-%{release}/
  s/%{dist}$//
}
/timestamp=/ d
" `find -name build.properties`

# Create Maven scripts
sed s/@MVN@/mvn/      %{SOURCE200} >mvn
sed s/@MVN@/mvnDebug/ %{SOURCE200} >mvnDebug
sed s/@MVN@/mvnyjp/   %{SOURCE200} >mvnyjp

# not really used during build, but a precaution
rm maven-ant-tasks-*.jar

# fix line endings
sed -i 's:\r::' *.txt

# fix for animal-sniffer (we don't generate 1.5 signatures)
sed -i 's:check-java-1.5-compat:check-java-1.6-compat:' pom.xml

rm -f apache-maven/src/bin/*.bat
sed -i 's:\r::' apache-maven/src/conf/settings.xml

# Update shell scripts to use unversioned classworlds
sed -i -e s:'-classpath "${M2_HOME}"/boot/plexus-classworlds-\*.jar':'-classpath "${M2_HOME}"/boot/plexus-classworlds.jar':g \
        apache-maven/src/bin/mvn*

# Disable animal-sniffer on RHEL
# Temporarily disabled for fedora to solve asm & asm4 clashing on classpath
#if [ %{?rhel} ]; then
%pom_remove_plugin :animal-sniffer-maven-plugin
#fi

%pom_add_dep org.codehaus.plexus:plexus-container-default maven-plugin-api

%build
# Put all JARs in standard location, but create symlinks in Maven lib
# directory so that Plexus Classworlds can find them.
%mvn_file ":{*}" %{name}/@1 %{_datadir}/%{name}/lib/@1

%mvn_build -- -Dproject.build.sourceEncoding=UTF-8

mkdir m2home
(cd m2home
    tar --delay-directory-restore -xvf ../apache-maven/target/*tar.gz
    chmod -R +rwX apache-%{name}-%{version}%{?ver_add}
    chmod -x apache-%{name}-%{version}%{?ver_add}/conf/settings.xml
)


%install
%mvn_install

export M2_HOME=$(pwd)/m2home/apache-maven-%{version}%{?ver_add}

install -d -m 755 %{buildroot}%{_datadir}/%{name}/bin
install -d -m 755 %{buildroot}%{_datadir}/%{name}/conf
install -d -m 755 %{buildroot}%{_datadir}/%{name}/boot
install -d -m 755 %{buildroot}%{_datadir}/%{name}/lib/ext
install -d -m 755 %{buildroot}%{_bindir}
install -d -m 755 %{buildroot}%{_sysconfdir}/%{name}
install -d -m 755 %{buildroot}%{_sysconfdir}/bash_completion.d
install -d -m 755 %{buildroot}%{_mandir}/man1

install -p -m 755 mvn %{buildroot}%{_bindir}/
install -p -m 755 mvnDebug %{buildroot}%{_bindir}/
install -p -m 755 mvnyjp %{buildroot}%{_bindir}/
install -p -m 644 %{SOURCE2} %{buildroot}%{_mandir}/man1
install -p -m 644 %{SOURCE1} %{buildroot}%{_sysconfdir}/bash_completion.d/%{name}
mv $M2_HOME/bin/m2.conf %{buildroot}%{_sysconfdir}
ln -sf %{_sysconfdir}/m2.conf %{buildroot}%{_datadir}/%{name}/bin/m2.conf
mv $M2_HOME/conf/settings.xml %{buildroot}%{_sysconfdir}/%{name}
ln -sf %{_sysconfdir}/%{name}/settings.xml %{buildroot}%{_datadir}/%{name}/conf/settings.xml

cp -a $M2_HOME/bin/* %{buildroot}%{_datadir}/%{name}/bin

ln -sf $(build-classpath plexus/classworlds) \
    %{buildroot}%{_datadir}/%{name}/boot/plexus-classworlds.jar

(cd %{buildroot}%{_datadir}/%{name}/lib
    # 1. atinject, aopalliance and objectweb-asm are bundled in
    #    sisu-inject-bean upstream normally
    # 2. httpcomponents-core, httpcomponents-client, commons-logging
    #    and commons-codec are bundled in wagon-http-shaded upstream
    #    normally
    build-jar-repository -s -p . \
        aether/aether-api \
        aether/aether-connector-wagon \
        aether/aether-impl \
        aether/aether-spi \
        aether/aether-util \
        commons-cli \
        plexus/plexus-cipher \
        plexus/containers-component-annotations \
        plexus/interpolation \
        plexus/plexus-sec-dispatcher \
        plexus/utils \
        guava \
        google-guice-no_aop \
        sisu/sisu-inject-bean \
        sisu/sisu-inject-plexus \
        maven-wagon/file \
        maven-wagon/http-shaded \
        maven-wagon/provider-api \
        \
        atinject \
        aopalliance \
        cglib \
        objectweb-asm/asm-all \
        \
        maven-wagon/http-shared4 \
        httpcomponents/httpclient \
        httpcomponents/httpcore \
        commons-logging \
        commons-codec \
)


%files -f .mfiles
%doc LICENSE.txt NOTICE.txt README.txt
%{_datadir}/%{name}
%{_bindir}/mvn*
%dir %{_javadir}/%{name}
%dir %{_sysconfdir}/%{name}
%config(noreplace) %{_sysconfdir}/m2.conf
%config(noreplace) %{_sysconfdir}/%{name}/settings.xml
%config(noreplace) %{_sysconfdir}/bash_completion.d/%{name}
%{_mandir}/man1/mvn.1.gz

%files javadoc -f .mfiles-javadoc
%doc LICENSE.txt NOTICE.txt


%changelog
* Tue Jul 21 2015 Michal Srb <msrb@redhat.com> - 3.0.5-17
- Access Maven Central via HTTPS by default
- Resolves: rhbz#1198561

* Mon Jan  6 2014 Mikolaj Izdebski <mizdebsk@redhat.com> - 3.0.5-16
- BuildRequire xmvn >= 1.3.0-5

* Fri Dec 27 2013 Daniel Mach <dmach@redhat.com> - 3.0.5-15
- Mass rebuild 2013-12-27

* Thu Nov  7 2013 Mikolaj Izdebski <mizdebsk@redhat.com> - 3.0.5-14
- Add cglib to plexus.core

* Wed Nov  6 2013 Mikolaj Izdebski <mizdebsk@redhat.com> - 3.0.5-13
- Add wagon-http-shared4 to plexus.core
- Add explcit requires

* Mon Oct 21 2013 Mikolaj Izdebski <mizdebsk@redhat.com> - 3.0.5-12
- Add missing dependencies to plexus.core
- Add patch for MNG-5402

* Wed Oct 16 2013 Stanislav Ochotnicky <sochotnicky@redhat.com> - 3.0.5-11
- Add objectweb-asm back to dependencies
- Resolves: rhbz#1019834

* Tue Oct 08 2013 Stanislav Ochotnicky <sochotnicky@redhat.com> - 3.0.5-10
- Rebuild and use no_aop guice
- Synchronize dependencies with upstream
- Resolves: rhbz#1016447

* Tue Sep 24 2013 Mikolaj Izdebski <mizdebsk@redhat.com> - 3.0.5-9
- Generate build number based on package release number

* Mon Jul 22 2013 Mikolaj Izdebski <mizdebsk@redhat.com> - 3.0.5-8
- Install mvnDebug and mvnyjp scripts
- Resolves: rhbz#986976

* Fri Jun 28 2013 Mikolaj Izdebski <mizdebsk@redhat.com> - 3.0.5-7
- Rebuild to regenerate API documentation
- Resolves: CVE-2013-1571

* Fri May 10 2013 Mikolaj Izdebski <mizdebsk@redhat.com> - 3.0.5-6
- Remove unneeded BR: async-http-client
- Add Requires on java-devel

* Thu May  2 2013 Mikolaj Izdebski <mizdebsk@redhat.com> - 3.0.5-5
- BR proper aether subpackages
- Resolves: rhbz#958160

* Fri Apr 26 2013 Mikolaj Izdebski <mizdebsk@redhat.com> - 3.0.5-4
- Add missing BuildRequires

* Tue Mar 12 2013 Mikolaj Izdebski <mizdebsk@redhat.com> - 3.0.5-3
- Make ext/ a subdirectory of lib/

* Tue Mar 12 2013 Mikolaj Izdebski <mizdebsk@redhat.com> - 3.0.5-2
- In maven-script don't override M2_HOME if already set

* Fri Mar  1 2013 Mikolaj Izdebski <mizdebsk@redhat.com> - 3.0.5-1
- Update to upstream version 3.0.5
- Move settings.xml to /etc

* Mon Feb 11 2013 Mikolaj Izdebski <mizdebsk@redhat.com> - 3.0.4-32
- Remove xerces-j2 from plexus.core realm
- Resolves: rhbz#784816

* Thu Feb  7 2013 Mikolaj Izdebski <mizdebsk@redhat.com> - 3.0.4-31
- Migrate BR from sisu to sisu subpackages

* Wed Feb  6 2013 Mikolaj Izdebski <mizdebsk@redhat.com> - 3.0.4-30
- Remove unneeded R: maven-local

* Fri Jan 25 2013 Mikolaj Izdebski <mizdebsk@redhat.com> - 3.0.4-29
- Drop support for local mode
- Build with xmvn, rely on auto-requires

* Wed Jan 23 2013 Mikolaj Izdebski <mizdebsk@redhat.com> - 3.0.4-28
- Move mvn-local and mvn-rpmbuild out of %_bindir

* Tue Nov 27 2012 Mikolaj Izdebski <mizdebsk@redhat.com> - 3.0.4-27
- Move some parts to maven-local package

* Thu Nov 22 2012 Mikolaj Izdebski <mizdebsk@redhat.com> - 3.0.4-26
- Force source >= 1.5 and target >= source

* Mon Nov 19 2012 Mikolaj Izdebski <mizdebsk@redhat.com> - 3.0.4-25
- Fix license tag

* Thu Nov 15 2012 Mikolaj Izdebski <mizdebsk@redhat.com> - 3.0.4-24
- Install NOTICE file with javadoc package

* Tue Nov 13 2012 Mikolaj Izdebski <mizdebsk@redhat.com> - 3.0.4-23
- Temporarly require Plexus POMs as a workaround

* Mon Nov 12 2012 Mikolaj Izdebski <mizdebsk@redhat.com> - 3.0.4-22
- Drop dependency on maven2-common-poms
- Drop support for /etc/maven/fragments

* Thu Nov 08 2012 Stanislav Ochotnicky <sochotnicky@redhat.com> - 3.0.4-21
- Add support for custom jar/pom/fragment directories

* Thu Nov  8 2012 Mikolaj Izdebski <mizdebsk@redhat.com> - 3.0.4-20
- Remove all slf4j providers except nop from maven realm

* Thu Nov  1 2012 Mikolaj Izdebski <mizdebsk@redhat.com> - 3.0.4-19
- Add aopalliance and cglib to maven-model-builder test dependencies

* Thu Nov  1 2012 Mikolaj Izdebski <mizdebsk@redhat.com> - 3.0.4-18
- Add objectweb-asm to classpath

* Thu Nov  1 2012 Mikolaj Izdebski <mizdebsk@redhat.com> - 3.0.4-17
- Add aopalliance, cglib, slf4j to classpath

* Wed Oct 31 2012 Mikolaj Izdebski <mizdebsk@redhat.com> - 3.0.4-16
- Don't echo JAVA_HOME in maven-script
- Add bash completion for -Dproject.build.sourceEncoding

* Mon Oct 29 2012 Mikolaj Izdebski <mizdebsk@redhat.com> - 3.0.4-15
- Add a few bash completion goals

* Wed Oct 24 2012 Stanislav Ochotnicky <sochotnicky@redhat.com> - 3.0.4-14
- Enable test skipping patch only for local mode (#869399)

* Fri Oct 19 2012 Stanislav Ochotnicky <sochotnicky@redhat.com> - 3.0.4-13
- Make sure we look for requested pom file and not resolved

* Thu Oct 18 2012 Stanislav Ochotnicky <sochotnicky@redhat.com> - 3.0.4-12
- Look into maven.repo.local first to handle corner-case packages (#865599)
- Finish handling of compatibility packages
- Disable animal-sniffer temporarily in Fedora as well

* Mon Aug 27 2012 Mikolaj Izdebski <mizdebsk@redhat.com> - 3.0.4-11
- Disable animal-sniffer on RHEL

* Wed Jul 25 2012 Stanislav Ochotnicky <sochotnicky@redhat.com> - 3.0.4-10
- Fix exit code of mvn-rpmbuild outside of mock
- Fix bug in compatibility jar handling

* Mon Jul 23 2012 Mikolaj Izdebski <mizdebsk@redhat.com> - 3.0.4-9
- Run redundant dependency checks only in mock

* Tue Jul 17 2012 Mikolaj Izdebski <mizdebsk@redhat.com> - 3.0.4-8
- Add manual page

* Mon Jun 11 2012 Mikolaj Izdebski <mizdebsk@redhat.com> - 3.0.4-7
- Implement redundant dependency checks

* Thu May 24 2012 Krzysztof Daniel <kdaniel@redhat.com> 3.0.4-6
- Bug 824789 -Use the version if it is possible.

* Mon May 14 2012 Stanislav Ochotnicky <sochotnicky@redhat.com> - 3.0.4-5
- Use Obsoletes instead of Conflicts

* Mon May 14 2012 Stanislav Ochotnicky <sochotnicky@redhat.com> - 3.0.4-4
- Obsolete and provide maven2

* Thu Mar 29 2012 Stanislav Ochotnicky <sochotnicky@redhat.com> - 3.0.4-3
- Make package noarch again to simplify bootstrapping

* Thu Feb  9 2012 Stanislav Ochotnicky <sochotnicky@redhat.com> - 3.0.4-2
- Make javadoc noarch
- Make compilation source level 1.5
- Fix borked tarball unpacking (reason unknown)

* Tue Jan 31 2012 Stanislav Ochotnicky <sochotnicky@redhat.com> - 3.0.4-1
- Update to latest upstream version

* Fri Jan 13 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.0.3-17
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Tue Dec 13 2011 Stanislav Ochotnicky <sochotnicky@redhat.com> - 3.0.3-16
- Add maven2-common-poms to Requires

* Tue Oct 11 2011 Stanislav Ochotnicky <sochotnicky@redhat.com> - 3.0.3-15
- Provide mvn script now instead of maven2
- Conflict with older versions of maven2

* Tue Aug 30 2011 Stanislav Ochotnicky <sochotnicky@redhat.com> - 3.0.3-14
- Fix test scope skipping

* Mon Aug 22 2011 Stanislav Ochotnicky <sochotnicky@redhat.com> - 3.0.3-13
- Remove unnecessary deps causing problems from lib/
- Add utf-8 source encoding patch

* Thu Jul 28 2011 Stanislav Ochotnicky <sochotnicky@redhat.com> - 3.0.3-12
- Disable debug package creation

* Thu Jul 28 2011 Stanislav Ochotnicky <sochotnicky@redhat.com> - 3.0.3-11
- Change to arch specific since we are using _libdir for _jnidir

* Tue Jul 26 2011 Stanislav Ochotnicky <sochotnicky@redhat.com> - 3.0.3-10
- Add bash completion (#706856)

* Mon Jul  4 2011 Stanislav Ochotnicky <sochotnicky@redhat.com> - 3.0.3-9
- Add resolving from jnidir and java-jni

* Thu Jun 23 2011 Stanislav Ochotnicky <sochotnicky@redhat.com> - 3.0.3-8
- Add maven-parent to BR/R

* Wed Jun 22 2011 Stanislav Ochotnicky <sochotnicky@redhat.com> - 3.0.3-7
- Process fragments in alphabetical order

* Tue Jun 21 2011 Stanislav Ochotnicky <sochotnicky@redhat.com> - 3.0.3-6
- Fix handling of fallback default_poms
- Add empty-dep into maven package to not require maven2 version

* Fri Jun 10 2011 Stanislav Ochotnicky <sochotnicky@redhat.com> - 3.0.3-5
- Process fragments directly instead of maven2-depmap.xml
- Expect fragments in /usr/share/maven-fragments
- Resolve poms also from /usr/share/maven-poms

* Mon Jun  6 2011 Stanislav Ochotnicky <sochotnicky@redhat.com> - 3.0.3-4
- Add help to mvn-rpmbuild and mvn-local (rhbz#710448)

* Tue May 10 2011 Stanislav Ochotnicky <sochotnicky@redhat.com> - 3.0.3-3
- Improve and clean up depmap handling for m2/m3 repos

* Mon Apr 18 2011 Stanislav Ochotnicky <sochotnicky@redhat.com> - 3.0.3-2
- Enable MAVEN_OPTS override in scripts

* Fri Mar  4 2011 Stanislav Ochotnicky <sochotnicky@redhat.com> - 3.0.3-1
- Update to 3.0.3
- Add ext subdirectory to lib

* Tue Mar  1 2011 Stanislav Ochotnicky <sochotnicky@redhat.com> - 3.0.3-0.1.rc1
- Update to 3.0.3rc1
- Enable tests again

* Thu Feb 10 2011 Stanislav Ochotnicky <sochotnicky@redhat.com> - 3.0.2-2
- Added mvn-rpmbuild script to be used in spec files
- mvn-local is now mixed mode (online with javadir priority)
- Changed mvn.jpp to mvn.local

* Fri Jan 28 2011 Stanislav Ochotnicky <sochotnicky@redhat.com> - 3.0.2-1
- Update to latest version (3.0.2)
- Ignore test failures temporarily

* Wed Jan 12 2011 Stanislav Ochotnicky <sochotnicky@redhat.com> - 3.0-6
- Fix bug #669034

* Tue Jan 11 2011 Stanislav Ochotnicky <sochotnicky@redhat.com> - 3.0-5
- Fix bugs #667625 #667614 and #667636
- Install maven metadata so they are not downloaded when mvn is run
- Rename mvn3-local to mvn-local
- Add more comments to resolver patch

* Tue Dec 21 2010 Stanislav Ochotnicky <sochotnicky@redhat.com> - 3.0-4
- Add fedora local resolver
- Fix quoting of arguments to mvn scripts
- Add javadoc subpackage
- Make jars versionless and remove unneeded clean section

* Wed Dec  1 2010 Stanislav Ochotnicky <sochotnicky@redhat.com> - 3.0-3
- Remove maven-ant-tasks jar in prep
- Make fragment file as %%config

* Tue Nov 16 2010 Stanislav Ochotnicky <sochotnicky@redhat.com> - 3.0-2
- Added apache-commons-parent to BR after commons changes

* Tue Oct 12 2010 Stanislav Ochotnicky <sochotnicky@redhat.com> - 3.0-1
- Initial package with vanilla maven (no jpp mode yet)
