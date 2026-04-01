	Release Notes for McAfee(R) VirusScan(R) for UNIX
                  Version 6.1.5
			Copyright (C) 2020 McAfee, LLC.
               All Rights Reserved


=====================================================

Thank you for using VirusScan(R) software. This
file contains important information regarding
this release. We recommend that you read the 
entire document.

Please ensure that you update the DAT files on your 
computer to the latest version.

    IMPORTANT:
    McAfee does not support automatic upgrading of a
    pre-release version of the software. To upgrade
    to a later beta release, a release candidate, or
    a production release of the software, you must
    first uninstall the existing version of the 
    software.


______________________________________________________
WHAT'S IN THIS FILE

-   New Features
-   System Requirements
-   Installation
    -   List of Files
    -   Removing the Software
-   Updating DAT Files
-   Known Issues
-   Known Limitation
-   Resolved Issues
-   Documentation
-   Engine End-of-Life (EOL) Program
    -   The Problem
    -   The Solution
    -   The Engine End-Of-Life Program
-   Contact Information
-   Copyright and Trademark Attributions
-   License Information


______________________________________________________
NEW FEATURES

v6.1.5

-	Includes new McAfee Anti-Malware Engine, version 6200

v6.1.4

-	Includes new McAfee Anti-Malware Engine, version 6100
-   Various Bug fixes

v6.1.3

-	Includes new McAfee Anti-Malware Engine, version 6010
-	Support for Microsoft Windows 10 Case Sensitivity

v6.1.2

-	Includes new McAfee Anti-Malware Engine, version 6000

v6.1.0

-   Includes new McAfee Anti-Malware Engine, version 5900

-   Switch --showencrypted display encrypted documents.
    This switch retains the 5800 reporting behavior while 
     scanning encrypted MS Office and PDF documents 
     (without this parameter, the 5900 engine by default reverts 
     to 5700 reporting behavior). The reporting of encrypted files
     is performed by using this parameter as these files are not 
     reported by default.

v6.0.6

-   Includes new McAfee Anti-Malware Engine, version 5800

-   Solaris 11 on SPARC is supported.

v6.0.5

-   Includes new McAfee Anti-Malware Engine, version 5700

-   IBM AIX 7.1 and Solaris 11 on Intel is supported.

-   Decompression of compressed DAT files by default

-   MD5 hash of every scanned file displayed in the scan.log

v6.0.4

-   Includes new McAfee Anti-Malware Engine, version 5600

v6.0.3

-   Hewlett-Packard HP-UX 11iv2 and 11iv3 on Intel Itanium is supported.

-   Hewlett-Packard HP-UX v11.00 is supported without any issues.

-   Switch --ignore-links functions as expected.

-   Switch --one-file-system functions as expected.

-   A new switch --ASCII has been added.
    This switch displays filenames as ASCII text.


______________________________________________________
SYSTEM REQUIREMENTS

Prerequisites:

-   The required version of the UNIX operating system 
    must be installed and running. 

-   You must have root account permissions to install
    the software. 


Disk space and Memory requirements:

-   At least 512 MB of free hard disk space

-   At least an additional 512 MB of free hard disk
    space reserved for temporary files

-   At least 512 MB of RAM for scanning operations 
    (1024 MB recommended minimum)

-   At least 1024 MB of RAM for updating operations


UNIX operating systems:

-   IBM AIX 6.1, 7.1, and 7.2 for RS6000 with the 
    latest maintenance packages installed.  

-   FreeBSD 9.x, 10.x for Intel with 
    legacy compatibility library libstdc++.so.5
    installed

-   Hewlett-Packard HP-UX 11iv3 
    for PA-RISC with the latest Standard HP-UX 
    patch bundles installed

-   Linux for Intel 32-bit distributions shipping 
    with version 2.6, 3.x or 4.x production kernels 
    with both libstdc++.so.5 (for engine) and
    libstdc++.so.6 installed.

-   Linux for Intel 64-bit distributions shipping 
    with version 2.6, 3.x or 4.x production kernels, 
    with libstdc++.so.6 installed

-   Sun Microsystems Solaris for SPARC versions 
    10 and 11 with the latest Solaris OS recommended
    cluster installed

-   Sun Microsystems Solaris for X86 versions 
    version 10 and 11 with the latest Solaris OS 
    recommended cluster installed


_________________________________________________________
INSTALLATION

1.  Download the appropriate distribution package for 
    your UNIX system to a temporary directory on your 
    computer.

    The distributions for evaluation or licensed 
    versions according to their operating systems are:
   ------------------------------------------------------
   Operating System		Package Name
   ------------------------------------------------------
   EVALUATION
       
       AIX              	vscl-aix-615-e.tar.gz
       FreeBSD          	vscl-bsd-615-e.tar.gz
       HP-UX            	vscl-hpx-615-e.tar.gz
       Linux            	vscl-l32-615-e.tar.gz
       Linux 64-bit     	vscl-l64-615-e.tar.gz
       Solaris SPARC    	vscl-sun-615-e.tar.gz
       Solaris X86      	vscl-s86-615-e.tar.gz

    LICENSED
      
       AIX              	vscl-aix-615-l.tar.gz
       FreeBSD          	vscl-bsd-615-l.tar.gz
       HP-UX            	vscl-hpx-615-l.tar.gz
       Linux            	vscl-132-615-l.tar.gz
       Linux 64-bit     	vscl-164-615-l.tar.gz
       Solaris SPARC    	vscl-sun-615-l.tar.gz
       Solaris X86      	vscl-s86-615-l.tar.gz


2.  Change to the directory where you downloaded
    your distribution package, then run the following
    commands:

      gunzip <package name>

      tar -xf <package name>

    Replace <package name> with the actual package 
    that you downloaded (without angled brackets).

    NOTE:
    The letter case of the package file might change
    while downloading the package. Check that the
    file name ends with an uppercase Z.

3.  Run the following at the command prompt:

      ./install-uvscan <installation directory>

    Replace <installation directory> with the target
    directory where you want to install the software 
    (without angled brackets). 
    
    The default installation directory is 
    /usr/local/uvscan.

    If the target installation directory that
    you specify does not exist, the script prompts you
    to create it.

    NOTE:
    To create an installation directory for the
    software, you must have the necessary WRITE
    and EXECUTE permissions.

    The script also prompts you to create symbolic links
    to the uvscan binary, the shared library, and man
    pages. We recommend that you create the default 
    links as shown in the wizard.

4.  If you do not want to create the default links or
    use a standard directory, set an environment 
    variable to the installation directory that you
    specified.
    The environment variables for the supported operating
    systems are:
   --------------------------------------------------------
    Operating System	 	Environment Variable
   --------------------------------------------------------
    AIX                  	LIBPATH
    FreeBSD             	LD_LIBRARY_PATH
    HP-UX                	SHLIB_PATH
    Linux                	LD_LIBRARY_PATH
    Linux 64-bit         	LD_LIBRARY_PATH
    Solaris SPARC        	LD_LIBRARY_PATH
    Solaris X86          	LD_LIBRARY_PATH


LIST OF FILES

The following files reside in the installation
directory of each distribution of the software.
   --------------------------------------------------------
    Filename		 	Details
   --------------------------------------------------------
    install-uvscan       	Installation script file
    uninstall-uvscan     	Uninstallation script file
    uvscan               	Executable file
    uvscan_secure        	Script, uses --secure option
    uvscancore           	Scan component
    config.dat           	Engine file
    license.dat          	License file 
    vcl615upg.pdf        	Product Guide
    license.txt          	License information
    readme.txt           	This file
    signlic.txt          	Third-party license information
    uvscan.1             	On-line help, 'man' pages
    
    libstdc++.so.6.0.8   	Support file
    libgcc_s.so.1        	Support file
    libstdc++.so.6       	Support file
    libgcc_s.a           	Support file
    libstdc++.a          	Support file
    
    
    

The installation adds one of the following library 
files to the installation directory, based on the 
distribution selected:

   ---------------------------------------------------
    Operating System	 	Filename
   ---------------------------------------------------
    AIX                  	libaixfv.a
    FreeBSD             	libbsdfv.so.4
    HP-UX                	libhpxfv.4
    Linux                	liblnxfv.so.4
    Linux 64-bit         	liblnxfv.so.4
    Solaris SPARC        	libsunfv.so.4
    Solaris X86          	libsunfv.so.4


The installation also adds one of the following symbolic 
links to the library, where required:
   ---------------------------------------------------
    Operating System	 	Symbolic link
   ---------------------------------------------------
    AIX                  	(not applicable)
    FreeBSD             	libbsdfv.so
    HP-UX                	libhpxfv.sl
    Linux                	liblnxfv.so
    Linux 64-bit         	liblnxfv.so
    Solaris SPARC        	libsunfv.so
    Solaris X86          	libsunfv.so


REMOVING THE SOFTWARE 

To remove the software by a script: 

1.  Change to the directory where you installed the
    software, then run the following command to start
    the uninstallation:

      ./uninstall-uvscan

2.  Follow the on-screen instructions and respond to 
    any prompts shown in the script to remove the
    program files from your computer.

3.  Delete the script uninstall-uvscan. 


To remove the software manually:

1.  Change to the directory where you installed the
    software.

2. Use the rm command to remove all the files 
   in that directory.

   If you created any symbolic links when you 
   installed the software, then you must delete 
   them manually to remove the software 
   completely from your computer.

   NOTE:
   To see a list of the files for each 
   UNIX distribution, see the "List of Files" section
   In this file.

__________________________________________________________
UPDATING DAT FILES

The DAT files are not included with the Command Line 
Scanner package and need to be separately downloaded and 
copied to the location where the Command Line Scanner is 
installed.

DAT files are contained in a single compressed file that 
one can download from the Internet.

1.  Navigate to the FTP location 
    ftp://ftp.mcafee.com/commonupdater/current/vscandat1000/dat/0000/

2.  To gain access, type anonymous as your user name 
    and your email address as the password when prompted.

3.  Look for a filename that is of the format 
    avvdat-nnnn.zip, where nnnn is the DAT version number. 
    This file contains the DAT files, compressed in ZIP 
    format.

The number given to the file changes on a regular basis.
A higher number indicates a later version of the DAT files.

To use the new DAT files:

1.  Create a download directory.

2.  Change to the download directory, and download the
    new compressed avvdat-nnnn.zip file.

3.  To extract the DAT files, type the command:

	unzip <file>

    Here, file is the name of the zip file you downloaded.

4.  Type the following command to move the DAT files 
    to the directory where your software is installed. 
    Name the file using lower case.

        mv *.dat installation-directory

    Here, installation-directory is the directory where
    you installed the software.

Your computer overwrites the old DAT files with the new 
files. Your anti-virus software will now use the new DAT 
files to scan for viruses.

Please refer to the command line scanner product guide
for a sample update script to automate downloading the
updated DAT files from the McAfee website.

__________________________________________________________
KNOWN ISSUES

1.  ISSUE:
    When mail clients using mailbox format similar to 
    concatenated MIME are scanned with MIME detection 
    enabled, they might result in unexpected errors such
    as "Files could not be opened".

    WORKAROUND:
    Exclude these files from scanning, or 
    use the --mailbox switch with --mime.

2.  ISSUE:
    The anti-malware Engine might need a large amount of 
    data space to decompress the heavily compressed files.  
    
    WORKAROUND: 
    Set the system's hard and soft data segment size 
    limits to "unlimited" or as large as possible. 
    Refer to the system's documentation for the 
    maximum size allowed for your environment.

3.  ISSUE:
    Scanning the content directories that do not 
    exist on disk (such as /proc, /sys, or /dev) might
    result in unwanted issues. 

    WORKAROUND:
    Exclude these directories from scanning using 
    the --exclude switch.

4.  ISSUE:
    After updating the DATs, VirusScan Command 
    Line Scanner on AIX may generate a core dump when run.

    WORKAROUND
    This issue is caused by the general memory model of 
    the AIX operating system. AIX by default has a segmented 
    memory architecture split into 256 MB segments, but 
    VirusScan Command Line Scanner 6.1.0 might require more 
    than a single 256 MB segment to execute.

    To resolve this specify the memory model to use when 
    running uvscan.

    Normally uvscan would be executed with the following 
    command:  ./uvscan <switch parameters> 

    However, AIX allows the user to directly specify the 
    memory model used by prefixing the executable 
    command with the environment variable: 
    LDR_CNTRL=MAXDATA=<memory model>@DSA 
    
    <memory model> is represented by a hexadecimal value.
    
    MAXDATA=0x80000000 sets the process memory limit 
    up to 2Gb. 
    
    @DSA forces AIX to use the very large memory model.

    This allows programs that require more than the 
    default 256MB memory segment to execute normally.

    For example: 

    Type the following command and press ENTER to 
    execute the scan process and decompress the DATs:

    LDR_CNTRL=MAXDATA=0x80000000@DSA ./uvscan --decompress

    Type the following command and press ENTER to
    execute the scan process and obtain the product version:

    LDR_CNTRL=MAXDATA=0x80000000@DSA ./uvscan --version

__________________________________________________________
KNOWN LIMITATION

EOL Platform:
- N/A for this release

__________________________________________________________
RESOLVED ISSUES

v6.1.5
	None

v6.1.4
	ISSUE
	1. Time format of the last line of command line scanner log file is not a valid time format
	2. Summary report format discrepancy
	3. Fix for CWE-274, more details on Security Bulletin - SB10316

v6.1.3
	None

v6.1.2  

1.  ISSUE:
	Scan of Japanese double- byte named file fails. (Reference ID: 1186832)

V6.1.0

1.  ISSUE:
    Scan summary does not match with the verbose scan output.

    (Reference ID: 1092975)

    RESOLUTION: The name of files which are not scanned are now 
    displayed verbose logging and matches with “NOT scanned” files under 
    scan summary.

V6.0.5
    None

V6.0.4
    None

v6.0.3

1.  ISSUE:
    VirusScan installs successfully on HP-UX v11.00. 
    However, scanning results in the following error:

    /usr/lib/dld.sl Unresolved symbol: wctob (code) 
    from /usr/local/uvscan/libstdc++.sl.6
    
    (Reference ID: 564098)

    RESOLUTION: Scans on HP-UX v11.00 functions as 
    expected.

2.  ISSUE:
    The --ignore-links switch does not function correctly.
   
    (Reference ID: 573914)

    RESOLUTION: The --ignore-links switch functions 
    as expected.

3.  ISSUE:
    The --one-file-system switch does not function
    correctly.
   
    (Reference ID: 565478)

    RESOLUTION: The --one-file-system switch functions 
    as expected.

4.  ISSUE:
    Filenames could be reported inconsistently in the 
    embedded objects. 

    (Reference ID: 560350)

    RESOLUTION: This is due to unavailability of codepage 
    information, which is required for encoding the text 
    in the correct character set. 
  
    If this information is available, the scanner sets 
    UTF-8 as default.
  
    If the character set uses extended codes, the scanner 
    uses its UTF-8 equivalent that appears to be garbled 
    text instead of file names.

    A switch --ASCII can be used to modify this behavior. 
    When this switch is used, the scanner displays 
    filenames as ASCII text.


__________________________________________________________
DOCUMENTATION

Documentation is included on the product package
and/or is available with a valid grant number
from the McAfee download site:

      https://www.mcafee.com/enterprise/en-us/downloads.html

   NOTE:
   Electronic copies of all product manuals are
   saved as Adobe Acrobat .PDF files. You can download 
   any version of Acrobat Reader from the Adobe website:

      https://get.adobe.com/reader/

This product includes the following documentation set:

-   Product Guide
    Introduces the product, describes product
    features, provides detailed instructions for
    configuring the software, deployment, and
    ongoing operation and maintenance.

-   Help system
    A Help file ('man' pages), accessed from
    within the software application, provides
    quick descriptions of the options.

-   A LICENSE Agreement
    The terms under which you may use the
    product. Read it carefully. If you install
    the product, you agree to the license
    terms.
 
-   Release Notes
    This README file.


__________________________________________________________
ENGINE END-OF-LIFE (EOL) PROGRAM

Your Anti-Virus software is only as good as its last
update!

Updating your DAT files and Anti-Virus Engine regularly
is essential and a MUST!

Sometimes architectural changes to the way that
the DAT files and Anti-Virus Engine work
together make it critical for you to update your
engine: an old engine WILL NOT catch some of today's
threats.

McAfee Labs recommends having as part of your
Security Policy Program, an Engine Update process to
take advantage of the latest technology and stay
protected!


THE PROBLEM

Thousands of new detections are added to the
DAT files daily by McAfee Labs. If you are not
up-to-date, you are vulnerable to any one of them
that gets a foothold in the field (also known as "in
the wild").

McAfee Labs releases regular DAT files,
ensuring that full protection is added to all McAfee
products. The DAT files contain the information
required to detect and remove threats - what to look
for and where to look for it.

However, today's threats are evolving almost on a
daily basis. Software providers continue to make
changes to operating systems and applications that
can change the way a program acts or works, and a
Anti-Virus program may not understand the
changes.


THE SOLUTION

Taking this into account, McAfee regularly
updates its Anti-Virus Engine used by ALL McAfee
virus-detection and removal products. The
engine understands all the different structures in
which a virus could lurk - EXE files, Microsoft
Office files, Linux files, and so on. Occasionally
these changes require us to make significant
architectural changes to the engine as well as the
DAT files.

McAfee Labs strongly recommends that users of ALL McAfee
Anti-Virus products update the engine in the 
products they have deployed as part of a
sound security best-practices program.

THE ENGINE END-OF-LIFE PROGRAM

To ensure protection from the evolving malicious code
threat, users should update as soon as possible upon
the release of McAfee's latest Anti-Virus Engine.

Engines begin their End of Life Process once a new
Engine version is released. Upon release of the new
engine version, the previous engine will be supported
for at most an additional 6 months, at the end of which
you will not be able to receive any further support on
the previous version.

Information on the McAfee Engine End-of-Life policy 
and a full list of supported engines and products 
can be found at:

       https://www.mcafee.com/enterprise/en-us/support/product-eol.html#product=scan_engine 

__________________________________________________________
CONTACT INFORMATION

    McAfee Labs Home Page
       https://www.mcafee.com/enterprise/en-us/threat-center/mcafee-labs.html

    McAfee Labs Threat Library
       https://www.mcafee.com/enterprise/en-us/threat-center.html

    Submit a Virus Sample
      https://www.mcafee.com/enterprise/en-us/threat-center/how-to-submit-sample.html

    DAT Notification Service
       https://sns.secure.mcafee.com/signup_login

DOWNLOAD SITE
    Home Page
       https://www.mcafee.com/enterprise/en-us/downloads.html

    Product Upgrades
       https://www.mcafee.com/enterprise/en-us/downloads/my-products.html

       Valid grant number required (contact Customer Service)

    Product End-of-Life Support
		https://www.mcafee.com/enterprise/en-us/support/product-eol.html


TECHNICAL SUPPORT
    Home Page
       https://support.mcafee.com/

    KnowledgeBase Search
       https://kc.mcafee.com

    McAfee Technical Support ServicePortal (Logon credentials required)
       https://mysupport.mcafee.com
       https://platinum.mcafee.com

    McAfee Support Notification Service  (SNS)
       https://sns.secure.mcafee.com/signup_login


CUSTOMER SERVICE
    US, Canada, and Latin America toll-free:
    Phone:    +1-888-VIRUS NO or +1-888-847-8766
              Monday-Friday, 8am-8pm, Central Time

    Web:      https://service.mcafee.com 


WORLDWIDE OFFICES
       https://www.mcafee.com/enterprise/en-us/home/contact-us.html

_____________________________________________________
COPYRIGHT AND TRADEMARK ATTRIBUTIONS

Copyright (C) 2020 McAfee, LLC. All Rights Reserved.
No part of this publication may be reproduced,
transmitted, transcribed, stored in a retrieval
system, or translated into any language in any form
or by any means without the written permission of
McAfee, LLC., or its suppliers or affiliate
companies.


TRADEMARK ATTRIBUTIONS

McAfee and the McAfee logo, McAfee Active Protection, 
McAfee DeepSAFE, ePolicy Orchestrator, McAfee ePO, McAfee EMM, McAfee 
Evader, Foundscore, Foundstone, Global Threat Intelligence, McAfee LiveSafe, 
Policy Lab, McAfee QuickClean, Safe Eyes, McAfee SECURE, McAfee Shredder, SiteAdvisor, McAfee Stinger, McAfee TechMaster, McAfee Total Protection, 
TrustedSource, VirusScan are registered trademarks or trademarks of McAfee, LLC.
 or its subsidiaries in the US and other countries. Other marks and brands may be
 claimed as the property of others.


_____________________________________________________
LICENSE INFORMATION

LICENSE AGREEMENT

NOTICE TO ALL USERS: CAREFULLY READ THE APPROPRIATE
LEGAL AGREEMENT CORRESPONDING TO THE LICENSE YOU
PURCHASED, WHICH SETS FORTH THE GENERAL TERMS AND
CONDITIONS FOR THE USE OF THE LICENSED SOFTWARE. IF
YOU DO NOT KNOW WHICH TYPE OF LICENSE YOU HAVE
ACQUIRED, PLEASE CONSULT THE SALES AND OTHER RELATED
LICENSE GRANT OR PURCHASE ORDER DOCUMENTS THAT
ACCOMPANIES YOUR SOFTWARE PACKAGING OR THAT YOU HAVE
RECEIVED SEPARATELY AS PART OF THE PURCHASE (AS A
BOOKLET, A FILE ON THE PRODUCT CD, OR A FILE
AVAILABLE ON THE WEBSITE FROM WHICH YOU DOWNLOADED
THE SOFTWARE PACKAGE). IF YOU DO NOT AGREE TO ALL OF
THE TERMS SET FORTH IN THE AGREEMENT, DO NOT INSTALL
THE SOFTWARE. IF APPLICABLE, YOU MAY RETURN THE
PRODUCT TO MCAFEE OR THE PLACE OF PURCHASE FOR A
FULL REFUND.


LICENSE ATTRIBUTIONS

This product includes or may include:

* Software originally written by Philip Hazel,
Copyright (c) 1997-2008 University of Cambridge. A
copy of the license agreement for this software can
be found at www.pcre.org/license.txt * This product 
includes software developed by the OpenSSL Project 
for use in the OpenSSL Toolkit (http://www.openssl.org/).
* Cryptographic software written by Eric A. Young
and software written by Tim J. Hudson. * Some
software programs that are licensed (or sublicensed)
to the user under the GNU General Public License
(GPL) or other similar Free Software licenses which,
among other rights, permit the user to copy, modify
and redistribute certain programs, or portions
thereof, and have access to the source code. The GPL
requires that for any software covered under the
GPL, which is distributed to someone in an
executable binary format, that the source code also
be made available to those users. For any such
software covered under the GPL, the source code is
made available on this CD. If any Free Software
licenses require that McAfee provide rights to use,
copy or modify a software program that are broader
than the rights granted in this agreement, then such
rights shall take precedence over the rights and
restrictions herein. * Software originally written
by Henry Spencer, Copyright 1992, 1993, 1994, 1997
Henry Spencer. * Software originally written by
Robert Nordier, Copyright (C) 1996-7 Robert Nordier.
* Software written by Douglas W. Sauder. * Software
developed by the Apache Software Foundation
(http://www.apache.org/). A copy of the license
agreement for this software can be found at
www.apache.org/licenses/LICENSE-2.0.txt.
* International Components for Unicode ("ICU")
Copyright (C) 1995-2002 International Business
Machines Corporation and others. * Software
developed by CrystalClear Software, Inc., Copyright
(C) 2000 CrystalClear Software, Inc. * FEAD(R)
Optimizer(R) technology, Copyright Netopsystems AG,
Berlin, Germany. * Outside In(R) Viewer Technology
(C) 1992-2001 Stellent Chicago, Inc. and/or Outside
In(R) HTML Export, (C) 2001 Stellent Chicago, Inc.
* Software copyrighted by Thai Open Source Software
Center Ltd. and Clark Cooper, (C) 1998, 1999, 2000.
* Software copyrighted by Expat maintainers.
* Software copyrighted by The Regents of the
University of California, (C) 1996, 1989, 1998-2000.
* Software copyrighted by Gunnar Ritter. * Software
copyrighted by Sun Microsystems, Inc., 4150 Network
Circle, Santa Clara, California 95054, U.S.A., (C)
2003. * Software copyrighted by Gisle Aas. (C)
1995-2003. * Software copyrighted by Michael A.
Chase, (C) 1999-2000. * Software copyrighted by Neil
Winton, (C) 1995-1996. * Software copyrighted by RSA
Data Security, Inc., (C) 1990-1992. * Software
copyrighted by Sean M. Burke, (C) 1999, 2000.
* Software copyrighted by Martijn Koster, (C) 1995.
* Software copyrighted by Brad Appleton, (C)
1996-1999. * Software copyrighted by Michael G.
Schwern, (C) 2001. * Software copyrighted by Graham
Barr, (C) 1998. * Software copyrighted by Larry Wall
and Clark Cooper, (C) 1998-2000. * Software
copyrighted by Frodo Looijaard, (C) 1997. * Software
copyrighted by the Python Software Foundation,
Copyright (C) 2001, 2002, 2003. A copy of the
license agreement for this software can be found at
www.python.org. * Software copyrighted by Beman
Dawes, (C) 1994-1999, 2002. * Software written by
Andrew Lumsdaine, Lie-Quan Lee, Jeremy G. Siek (C)
1997-2000 University of Notre Dame. * Software
copyrighted by Simone Bordet & Marco Cravero, (C)
2002. * Software copyrighted by Stephen Purcell, (C)
2001. * Software developed by the Indiana University
Extreme! Lab (http://www.extreme.indiana.edu/).
* Software copyrighted by International Business
Machines Corporation and others, (C) 1995-2003.
* Software developed by the University of
California, Berkeley and its contributors.
* Software developed by Ralf S. Engelschall
<rse@engelschall.com> for use in the mod_ssl project
(http://www.modssl.org/). * Software copyrighted by
Kevlin Henney, (C) 2000-2002. * Software copyrighted
by Peter Dimov and Multi Media Ltd. (C) 2001, 2002.
* Software copyrighted by David Abrahams, (C) 2001,
2002. See http://www.boost.org/libs/bind/bind.html
for documentation. * Software copyrighted by Steve
Cleary, Beman Dawes, Howard Hinnant & John Maddock,
(C) 2000. * Software copyrighted by Boost.org, (C)
1999-2002. * Software copyrighted by Nicolai M.
Josuttis, (C) 1999. * Software copyrighted by Jeremy
Siek, (C) 1999-2001. * Software copyrighted by
Daryle Walker, (C) 2001. * Software copyrighted by
Chuck Allison and Jeremy Siek, (C) 2001, 2002.
* Software copyrighted by Samuel Krempp, (C) 2001.
See http://www.boost.org for updates, documentation,
and revision history. * Software copyrighted by Doug
Gregor (gregod@cs.rpi.edu), (C) 2001, 2002.
* Software copyrighted by Cadenza New Zealand Ltd.,
(C) 2000. * Software copyrighted by Jens Maurer,
(C) 2000, 2001. * Software copyrighted by Jaakko
Jarvi (jaakko.jarvi@cs.utu.fi), (C) 1999, 2000.
* Software copyrighted by Ronald Garcia, (C) 2002.
* Software copyrighted by David Abrahams, Jeremy
Siek, and Daryle Walker, (C) 1999-2001. * Software
copyrighted by Stephen Cleary (shammah@voyager.net),
(C) 2000. * Software copyrighted by Housemarque Oy
<http://www.housemarque.com>, (C) 2001. * Software
copyrighted by Paul Moore, (C) 1999. * Software
copyrighted by Dr. John Maddock, (C) 1998-2002.
* Software copyrighted by Greg Colvin and Beman
Dawes, (C) 1998, 1999. * Software copyrighted by
Peter Dimov, (C) 2001, 2002. * Software copyrighted
by Jeremy Siek and John R. Bandela, (C) 2001.
* Software copyrighted by Joerg Walter and Mathias
Koch, (C) 2000-2002. * Software copyrighted by
Carnegie Mellon University (C) 1989, 1991, 1992.
* Software copyrighted by Cambridge Broadband Ltd.,
(C) 2001-2003. * Software copyrighted by Sparta,
Inc., (C) 2003-2004. * Software copyrighted by
Cisco, Inc and Information Network Center of Beijing
University of Posts and Telecommunications, (C)
2004. * Software copyrighted by Simon Josefsson, (C)
2003. * Software copyrighted by Thomas Jacob, (C)
2003-2004. * Software copyrighted by Advanced
Software Engineering Limited, (C) 2004. * Software
copyrighted by Todd C. Miller, (C) 1998. * Software
copyrighted by The Regents of the University of
California, (C) 1990, 1993, with code derived from
software contributed to Berkeley by Chris Torek.

The following 3rd-party software terms apply or 
may apply:

Boost Software License - Version 1.0 - August 17th, 2003
--------------------------------------------------------

Permission is hereby granted, free of charge, 
to any person or organization obtaining a copy of 
the software and accompanying documentation covered 
by this license (the "Software") to use, reproduce, 
display, distribute, execute, and transmit the 
Software, and to prepare derivative works of the 
Software, and to permit third-parties to whom the 
Software is furnished to do so, all subject to the 
following:

The copyright notices in the Software and this entire 
statement, including the above license grant, this 
restriction and the following disclaimer, must be 
included in all copies of the Software, in whole or
in part, and all derivative works of the Software, 
unless such copies or derivative works are solely in 
the form of machine-executable object code generated 
by a source language processor.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF 
ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED 
TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A 
PARTICULAR PURPOSE, TITLE AND NON-INFRINGEMENT. IN NO 
EVENT SHALL THE COPYRIGHT HOLDERS OR ANYONE DISTRIBUTING 
THE SOFTWARE BE LIABLE FOR ANY DAMAGES OR OTHER 
LIABILITY, WHETHER IN CONTRACT, TORT OR OTHERWISE, 
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE 
OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


PCRE LICENCE
------------
PCRE is a library of functions to support regular 
expressions whose syntax and semantics are as close as 
possible to those of the Perl 5 language.

Release 7 of PCRE is distributed under the terms of 
the "BSD" licence, as specified below. The 
documentation for PCRE, supplied in the "doc" 
directory, is distributed under the same terms as 
the software itself.

The basic library functions are written in C and 
are freestanding. Also included in the distribution 
is a set of C++ wrapper functions.


THE BASIC LIBRARY FUNCTIONS
---------------------------
Written by:        Philip Hazel
Email local part:  ph10
Email domain:      cam.ac.uk

University of Cambridge Computing Service, Cambridge, England.

Copyright (c) 1997-2007 University of Cambridge. All rights reserved.


THE C++ WRAPPER FUNCTIONS
-------------------------
Contributed by:    Google Inc.

Copyright (c) 2007, Google Inc. All rights reserved.


THE "BSD" LICENCE
-----------------
Redistribution and use in source and binary forms, 
with or without modification, are permitted provided 
that the following conditions are met:

* Redistributions of source code must retain the 
above copyright notice, this list of conditions and 
the following disclaimer.

* Redistributions in binary form must reproduce the 
above copyright notice, this list of conditions and the 
following disclaimer in the documentation and/or other 
materials provided with the distribution.

* Neither the name of the University of Cambridge nor 
the name of Google Inc. nor the names of their 
contributors may be used to endorse or promote products 
derived from this software without specific prior 
written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND 
CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED 
WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED 
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A 
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL 
THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY 
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR 
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, 
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF 
USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) 
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER 
IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING 
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE 
USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE 
POSSIBILITY OF SUCH DAMAGE.


             GNU GENERAL PUBLIC LICENSE
                Version 2, June 1991

Copyright (C) 1989, 1991 Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA
02110-1301 USA
Everyone is permitted to copy and distribute
verbatim copies of this license document, but
changing it is not allowed.

                      Preamble

The licenses for most software are designed to take
away your freedom to share and change it. By
contrast, the GNU General Public License is intended
to guarantee your freedom to share and change free
software--to make sure the software is free for all
its users.  This General Public License applies to
most of the Free Software Foundation's software and
to any other program whose authors commit to using
it.  (Some other Free Software Foundation software
is covered by the GNU Lesser General Public License
instead.)  You can apply it to your programs, too.

When we speak of free software, we are referring to
freedom, not price.  Our General Public Licenses are
designed to make sure that you have the freedom to
distribute copies of free software (and charge for
this service if you wish), that you receive source
code or can get it if you want it, that you can
change the software or use pieces of it in new free
programs; and that you know you can do these
things.

To protect your rights, we need to make restrictions
that forbid anyone to deny you these rights or to
ask you to surrender the rights. These restrictions
translate to certain responsibilities for you if you
distribute copies of the software, or if you modify
it.

For example, if you distribute copies of such a
program, whether gratis or for a fee, you must give
the recipients all the rights that you have.  You
must make sure that they, too, receive or can get
the source code.  And you must show them these terms
so they know their rights.

We protect your rights with two steps: (1) copyright
the software, and (2) offer you this license which
gives you legal permission to copy, distribute
and/or modify the software.

Also, for each author's protection and ours, we want
to make certain that everyone understands that there
is no warranty for this free software.  If the
software is modified by someone else and passed on,
we want its recipients to know that what they have
is not the original, so that any problems introduced
by others will not reflect on the original authors'
reputations.

Finally, any free program is threatened constantly
by software patents.  We wish to avoid the danger
that redistributors of a free program will
individually obtain patent licenses, in effect
making the program proprietary.  To prevent this, we
have made it clear that any patent must be licensed
for everyone's free use or not licensed at all.

The precise terms and conditions for copying,
distribution and modification follow.

             GNU GENERAL PUBLIC LICENSE
 TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND
                    MODIFICATION

0. This License applies to any program or other work
which contains a notice placed by the copyright
holder saying it may be distributed under the terms
of this General Public License.  The "Program",
below, refers to any such program or work, and a
"work based on the Program" means either the Program
or any derivative work under copyright law: that is
to say, a work containing the Program or a portion
of it, either verbatim or with modifications and/or
translated into another language.  (Hereinafter,
translation is included without limitation in the
term "modification".)  Each licensee is addressed as
"you".

Activities other than copying, distribution and
modification are not covered by this License; they
are outside its scope.  The act of running the
Program is not restricted, and the output from the
Program is covered only if its contents constitute a
work based on the Program (independent of having
been made by running the Program). Whether that is
true depends on what the Program does.

1. You may copy and distribute verbatim copies of
the Program's source code as you receive it, in any
medium, provided that you conspicuously and
appropriately publish on each copy an appropriate
copyright notice and disclaimer of warranty; keep
intact all the notices that refer to this License
and to the absence of any warranty; and give any
other recipients of the Program a copy of this
License along with the Program.

You may charge a fee for the physical act of
transferring a copy, and you may at your option
offer warranty protection in exchange for a fee.

2. You may modify your copy or copies of the Program
or any portion of it, thus forming a work based on
the Program, and copy and distribute such
modifications or work under the terms of Section 1
above, provided that you also meet all of these
conditions:

a) You must cause the modified files to carry
prominent notices stating that you changed the files
and the date of any change.

b) You must cause any work that you distribute or
publish, that in whole or in part contains or is
derived from the Program or any part thereof, to be
licensed as a whole at no charge to all third
parties under the terms of this License.

c) If the modified program normally reads commands
interactively when run, you must cause it, when
started running for such interactive use in the most
ordinary way, to print or display an announcement
including an appropriate copyright notice and a
notice that there is no warranty (or else, saying
that you provide a warranty) and that users may
redistribute the program under these conditions, and
telling the user how to view a copy of this License.
(Exception: if the Program itself is interactive but
does not normally print such an announcement, your
work based on the Program is not required to print
an announcement.)

These requirements apply to the modified work as a
whole.  If identifiable sections of that work are
not derived from the Program, and can be reasonably
considered independent and separate works in
themselves, then this License, and its terms, do not
apply to those sections when you distribute them as
separate works.  But when you distribute the same
sections as part of a whole which is a work based on
the Program, the distribution of the whole must be
on the terms of this License, whose permissions for
other licensees extend to the entire whole, and thus
to each and every part regardless of who wrote it.

Thus, it is not the intent of this section to claim
rights or contest your rights to work written
entirely by you; rather, the intent is to exercise
the right to control the distribution of derivative
or collective works based on the Program.

In addition, mere aggregation of another work not
based on the Program with the Program (or with a
work based on the Program) on a volume of a storage
or distribution medium does not bring the other work
under the scope of this License.

3. You may copy and distribute the Program (or a
work based on it, under Section 2) in object code or
executable form under the terms of Sections 1 and 2
above provided that you also do one of the
following:

a) Accompany it with the complete corresponding
machine-readable source code, which must be
distributed under the terms of Sections 1 and 2
above on a medium customarily used for software
interchange; or,

b) Accompany it with a written offer, valid for at
least three years, to give any third party, for a
charge no more than your cost of physically
performing source distribution, a complete
machine-readable copy of the corresponding source
code, to be distributed under the terms of Sections
1 and 2 above on a medium customarily used for
software interchange; or,

c) Accompany it with the information you received as
to the offer to distribute corresponding source
code.  (This alternative is allowed only for
noncommercial distribution and only if you received
the program in object code or executable form with
such an offer, in accord with Subsection b above.)

The source code for a work means the preferred form
of the work for making modifications to it.  For an
executable work, complete source code means all the
source code for all modules it contains, plus any
associated interface definition files, plus the
scripts used to control compilation and installation
of the executable.  However, as a special exception,
the source code distributed need not include
anything that is normally distributed (in either
source or binary form) with the major components
(compiler, kernel, and so on) of the operating
system on which the executable runs, unless that
component itself accompanies the executable.

If distribution of executable or object code is made
by offering access to copy from a designated place,
then offering equivalent access to copy the source
code from the same place counts as distribution of
the source code, even though third parties are not
compelled to copy the source along with the object
code.

4. You may not copy, modify, sublicense, or
distribute the Program except as expressly provided
under this License.  Any attempt otherwise to copy,
modify, sublicense or distribute the Program is
void, and will automatically terminate your rights
under this License. However, parties who have
received copies, or rights, from you under this
License will not have their licenses terminated so
long as such parties remain in full compliance.

5. You are not required to accept this License,
since you have not signed it.  However, nothing else
grants you permission to modify or distribute the
Program or its derivative works.  These actions are
prohibited by law if you do not accept this License.
Therefore, by modifying or distributing the Program
(or any work based on the Program), you indicate
your acceptance of this License to do so, and all
its terms and conditions for copying, distributing
or modifying the Program or works based on it.

6. Each time you redistribute the Program (or any
work based on the Program), the recipient
automatically receives a license from the original
licensor to copy, distribute or modify the Program
subject to these terms and conditions.  You may not
impose any further restrictions on the recipients'
exercise of the rights granted herein. You are not
responsible for enforcing compliance by third
parties to this License.

7. If, as a consequence of a court judgment or
allegation of patent infringement or for any other
reason (not limited to patent issues), conditions
are imposed on you (whether by court order,
agreement or otherwise) that contradict the
conditions of this License, they do not excuse you
from the conditions of this License.  If you cannot
distribute so as to satisfy simultaneously your
obligations under this License and any other
pertinent obligations, then as a consequence you may
not distribute the Program at all.  For example, if
a patent license would not permit royalty-free
redistribution of the Program by all those who
receive copies directly or indirectly through you,
then the only way you could satisfy both it and this
License would be to refrain entirely from
distribution of the Program.

If any portion of this section is held invalid or
unenforceable under any particular circumstance, the
balance of the section is intended to apply and the
section as a whole is intended to apply in other
circumstances.

It is not the purpose of this section to induce you
to infringe any patents or other property right
claims or to contest validity of any such claims;
this section has the sole purpose of protecting the
integrity of the free software distribution system,
which is implemented by public license practices.
Many people have made generous contributions to the
wide range of software distributed through that
system in reliance on consistent application of that
system; it is up to the author/donor to decide if he
or she is willing to distribute software through any
other system and a licensee cannot impose that
choice.

This section is intended to make thoroughly clear
what is believed to be a consequence of the rest of
this License.

8. If the distribution and/or use of the Program is
restricted in certain countries either by patents or
by copyrighted interfaces, the original copyright
holder who places the Program under this License may
add an explicit geographical distribution limitation
excluding those countries, so that distribution is
permitted only in or among countries not thus
excluded.  In such case, this License incorporates
the limitation as if written in the body of this
License.

9. The Free Software Foundation may publish revised
and/or new versions of the General Public License
from time to time.  Such new versions will be
similar in spirit to the present version, but may
differ in detail to address new problems or
concerns.

Each version is given a distinguishing version
number.  If the Program specifies a version number
of this License which applies to it and "any later
version", you have the option of following the terms
and conditions either of that version or of any
later version published by the Free Software
Foundation.  If the Program does not specify a
version number of this License, you may choose any
version ever published by the Free Software
Foundation.

10. If you wish to incorporate parts of the Program
into other free programs whose distribution
conditions are different, write to the author to ask
for permission.  For software which is copyrighted
by the Free Software Foundation, write to the Free
Software Foundation; we sometimes make exceptions
for this.  Our decision will be guided by the two
goals of preserving the free status of all
derivatives of our free software and of promoting
the sharing and reuse of software generally.

                     NO WARRANTY

11. BECAUSE THE PROGRAM IS LICENSED FREE OF CHARGE,
THERE IS NO WARRANTY FOR THE PROGRAM, TO THE EXTENT
PERMITTED BY APPLICABLE LAW.  EXCEPT WHEN OTHERWISE
STATED IN WRITING THE COPYRIGHT HOLDERS AND/OR OTHER
PARTIES PROVIDE THE PROGRAM "AS IS" WITHOUT WARRANTY
OF ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING,
BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS FOR A PARTICULAR
PURPOSE.  THE ENTIRE RISK AS TO THE QUALITY AND
PERFORMANCE OF THE PROGRAM IS WITH YOU.  SHOULD THE
PROGRAM PROVE DEFECTIVE, YOU ASSUME THE COST OF ALL
NECESSARY SERVICING, REPAIR OR CORRECTION.

12. IN NO EVENT UNLESS REQUIRED BY APPLICABLE LAW OR
AGREED TO IN WRITING WILL ANY COPYRIGHT HOLDER, OR
ANY OTHER PARTY WHO MAY MODIFY AND/OR REDISTRIBUTE
THE PROGRAM AS PERMITTED ABOVE, BE LIABLE TO YOU FOR
DAMAGES, INCLUDING ANY GENERAL, SPECIAL, INCIDENTAL
OR CONSEQUENTIAL DAMAGES ARISING OUT OF THE USE OR
INABILITY TO USE THE PROGRAM (INCLUDING BUT NOT
LIMITED TO LOSS OF DATA OR DATA BEING RENDERED
INACCURATE OR LOSSES SUSTAINED BY YOU OR THIRD
PARTIES OR A FAILURE OF THE PROGRAM TO OPERATE WITH
ANY OTHER PROGRAMS), EVEN IF SUCH HOLDER OR OTHER
PARTY HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH
DAMAGES.

             END OF TERMS AND CONDITIONS

    How to Apply These Terms to Your New Programs

If you develop a new program, and you want it to be
of the greatest possible use to the public, the best
way to achieve this is to make it free software
which everyone can redistribute and change under
these terms.

To do so, attach the following notices to the
program.  It is safest to attach them to the start
of each source file to most effectively convey the
exclusion of warranty; and each file should have at
least the "copyright" line and a pointer to where
the full notice is found.

<one line to give the program's name and a brief
idea of what it does.>
Copyright (C) <year>  <name of author>

This program is free software; you can redistribute
it and/or modify it under the terms of the GNU
General Public License as published by the Free
Software Foundation; either version 2 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will
be useful, but WITHOUT ANY WARRANTY; without even
the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE.  See the GNU General
Public License for more details.

You should have received a copy of the GNU General
Public License along with this program; if not,
write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA
02110-1301 USA.

Also add information on how to contact you by
electronic and paper mail.

If the program is interactive, make it output a
short notice like this when it starts in an
interactive mode:

Gnomovision version 69, Copyright (C) year name of
author Gnomovision comes with ABSOLUTELY NO
WARRANTY; for details type `show w'. This is free
software, and you are welcome to redistribute it
under certain conditions; type `show c' for
details.

The hypothetical commands `show w' and `show c'
should show the appropriate parts of the General
Public License.  Of course, the commands you use may
be called something other than `show w' and `show
c'; they could even be mouse-clicks or menu
items--whatever suits your program.

You should also get your employer (if you work as a
programmer) or your school, if any, to sign a
"copyright disclaimer" for the program, if
necessary.  Here is a sample; alter the names:

Yoyodyne, Inc., hereby disclaims all copyright
interest in the program `Gnomovision' (which makes
passes at compilers) written by James Hacker.

<signature of Ty Coon>, 1 April 1989
Ty Coon, President of Vice

This General Public License does not permit
incorporating your program into proprietary
programs.  If your program is a subroutine library,
you may consider it more useful to permit linking
proprietary applications with the library.  If this
is what you want to do, use the GNU Lesser General
Public License instead of this License.



DBN 011-EN 
RMID WINDOWS
Deriv. V3.1.4

