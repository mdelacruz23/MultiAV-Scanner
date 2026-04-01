#!/bin/sh
# Copyright (c) 2019 McAfee, Inc. All Rights Reserved.
# required programs: tar|unzip, wget|curl, sed, awk, echo, cut, ls, printf
#
#============================================================
# defaults: do not modify
#============================================================
unset md5checker leave_files debug

#============================================================
# change these variables to match your environment
#============================================================
# install_dir must be a directory and writable
install_dir=`dirname "$0"`
#
# tmp_dir must be a directory and writable
tmp_dir="/tmp/scanners_defs/mcafee"
#
# optional: this prg is responsible for calculating the md5 for a file
md5checker="md5sum"
#
# The package type that the DATs will be downloaded in. Set it to
# TAR to get the DATs in a tar archive. Set it to ZIP to get the
# DATs in a ZIP archive.
#PACKAGE_TYPE="TAR"
PACKAGE_TYPE="ZIP"

#============================================================
# change these variables to set your preferences
#============================================================
# set to non-empty to leave downloaded files after the update is done
#leave_files="true"
#
# show debug messages (set to non-empty to enable)
#debug=yes
#
# set to non-empty to use curl for downloading
# otherwise, wget is used by default
#use_curl=yes

#============================================================
# these variables are normally best left unmodified
#============================================================
UVSCAN_EXE="uvscan"
UVSCAN_SWITCHES=""

#============================================================
Cleanup()
{
	if [ -z "$leave_files" ] ; then
		for f in "$avvdat_ini" "$download" ; do
			[ -n "$f" -a -e "$f" ] && rm -f "$f"
		done
	fi
}
exit_error()
{
	[ -n "$1" ] && printf "$prgname: ERROR: $1\n"
	Cleanup ; exit 1
}
print_debug()
{
	[ -n "$debug" ] && printf "$prgname: [debug] $@\n"
}

# Function to parse avvdat.ini and return, via stdout, the
# contents of a specified section. Requires the avvdat.ini
# file to be available on stdin.
# $1 - Section name
FindINISection()
{
	unset section_found
	
	section_name="[$1]"
	while read line ; do
		if [ "$line" = "$section_name" ] ; then
			section_found="true"
		elif [ -n "$section_found" ] ; then
			if [ "`echo $line | cut -c1`" != "[" ] ; then
				[ -n "$line" ] && printf "$line\n"
			else
				unset section_found
			fi
		fi
	done
}

# Function to return the DAT version currently installed for
# use with the command line scanner
# $1 - uvscan exe (including path)
# $2 - any extra switches for uvscan
GetCurrentDATVersion()
{
	dirname=`dirname "$1"`
	uvscan_bin=`basename "$1"`

	output=`(cd "$dirname"; "./$uvscan_bin" $2 --version )`
	[ $? -eq 0 ] || return 1

	lversion=`printf "$output\n" | grep "Dat set version:" |
		cut -d' ' -f4`
	printf "${lversion}.0\n"

	return 0
}

# Function to download a specified file from ftp.nai.com
# $1 - Path on ftp server
# $2 - name of file to download.
# $3 - download type (either bin or ascii)
# $4 - download directory
# DownloadFile()
# {
# 	[ "$3" = "bin" -o "$3" = "ascii" ] || return 1
# 	dtype="$3"
# 
# 	if [ -n "$use_curl" ] ; then
# 		print_debug "using curl to download files..."
# 		print_debug "downloading file '$2' into '$4'"
# 		echo " \
# 		curl http://update.nai.com/$1/$2 \
# 		-o $4/$2 \
# 		-s" | sh || return 1
# 	else
# 		print_debug "using wget to download files..."
# 		print_debug "downloading file '$2' into '$4'"
# 		echo " \
# 		wget http://update.nai.com/$1/$2 \
# 		-O $4/$2 \
# 		-q -r" | sh || return 1
# 	fi
# 	
# 	return 0
# }

# Function to check the specified file against its expected size, checksum and MD5 checksum.
# $1 - File name (including path)
# $2 - expected size
# $3 - MD5 Checksum
ValidateFile()
{
	# Check the file size matches what we expect...
	size=`ls -l "$1" | awk ' { print $5 } '`
	[ -n "$size" -a "$size" = "$2" ] || return 1

	# make md5 check optional. return "success" if there's no support
	[ -z "$md5checker" -o "(" ! -x "`which $md5checker 2> /dev/null`" \
	")" ] && return 0

	# Check the md5 checksum...
	md5_csum=`$md5checker "$1" 2>/dev/null | cut -d' ' -f1`
	[ -n "$md5_csum" -a "$md5_csum" = "$3" ] # return code
}

# Function to extract the listed files from the given zip file.
# $1 - directory to install to
# $2 - downloaded file.
# $3 - list of files to install
Update_ZIP()
{
	unset flist
	for file in $3 ; do
		fname=`printf "$file\n" | awk -F':' ' { print $1 } '`
		flist="$flist $fname"
	done

	# Backup any files about to be updated...
	[ ! -d "backup" ] && mkdir backup 2>/dev/null
	[ -d "backup" ] && cp $flist "backup" 2>/dev/null

	# Update the DAT files.
	print_debug "uncompressing '$2'..."
        cp $2 ${2}.orig
	unzip -o -d $1 $2 $flist >/dev/null || return 1
        mv ${2}.orig $2
	for file in $3 ; do
		fname=`printf "$file\n" | awk -F':' ' { print $1 } '`
		permissions=`printf "$file\n" | awk -F':' ' { print $NF } '`
		chmod "$permissions" "$1/$fname"
	done
	
	return 0
}

Update_TAR()
{
    unset flist
    for file in $3 ; do
        fname=`printf "$file\n" | awk -F':' ' { print $1 } '`
        flist="$flist $fname"
    done
    
    # Backup any files about to be updated...
    [ ! -d "backup" ] && mkdir backup 2>/dev/null
    [ -d "backup" ] && cp $flist backup 2>/dev/null
    
    # Update the DAT files.
	print_debug "extracting '$2'..."
    cat $2 2>/dev/null | (cd $1 ; tar -xf - $flist >/dev/null 2>/dev/null ) || return 1
    
    for file in $3 ; do
        fname=`printf "$file\n" | awk -F':' ' { print $1 } '`
        permissions=`printf "$file\n" | awk -F':' ' { print $NF } '`
        chmod "$permissions" "$1/$fname"
    done
    
    return 0
}

# globals
prgname=`basename "$0"`
prgname="${prgname%.*}"
unset perform_update avvdat_ini download

# sanity checks
[ -d "$tmp_dir" ] || mkdir -p "$tmp_dir" 2>/dev/null
[ -d "$tmp_dir" ] || exit_error "directory '$tmp_dir' does not exist."
[ -x "$install_dir/$UVSCAN_EXE" ] \
|| exit_error "could not find uvscan executable"

# Download avvdat ini to parse the DAT set properties (version, location, etc.)
# DownloadFile "products/commonupdater" "avvdat.ini" "ascii" "$tmp_dir" \
# || exit_error "downloading avvdat.ini"
avvdat_ini="$tmp_dir/avvdat.ini"

# Did we get avvdat.ini?
[ -r "$avvdat_ini" ] || exit_error "unable to get avvdat.ini file"

ini_section=AVV-$PACKAGE_TYPE
file_list="avvscan.dat:444 avvnames.dat:444 avvclean.dat:444"

# Get the version of the installed DATs...
current_version=`GetCurrentDATVersion "$install_dir/$UVSCAN_EXE" "$UVSCAN_SWITCHES"`
[ -n "$current_version" ] \
|| exit_error "unable to get currently installed DAT version."
current_major=`echo "$current_version" | cut -d. -f-1`
current_minor=`echo "$current_version" | cut -d. -f2-`

# curl and wget transfers text without EOL conversion
# converting ascii transfers to *nix EOL in the downloaded INI file
sed -i 's/\r//g' "$avvdat_ini"

# parse INI file
INISection=`FindINISection "$ini_section" < $avvdat_ini`
[ -n "$INISection" ] \
|| exit_error "unable to get section $ini_section from avvdat.ini"

unset major_ver file_name file_path file_size md5
# Some INI sections have the MinorVersion field missing.
minor_ver=0 # To work around this, we will initialise it to 0.

# Parse the section and keep what we are interested in.
for field in $INISection ; do
	name=`echo "$field" | awk -F'=' ' { print $1 } '`
	value=`echo "$field" | awk -F'=' ' { print $2 } '`
	case $name in
		"DATVersion") major_ver=$value ;; # available: major
		"MinorVersion") minor_ver=$value ;; # available: minor
		"FileName") file_name="$value" ;; # file to download
		"FilePath") file_path=$value ;; # path on FTP server
		"FileSize") file_size=$value ;; # file size
		"MD5") md5=$value ;; # MD5 checksum
	esac
done

# sanity check
[ -n "$major_ver" -a -n "$minor_ver" -a -n "$file_name" \
-a -n "$file_path" -a -n "$file_size" -a -n "$md5" ] \
|| exit_error "avvdat.ini: '[$ini_section]' has incomplete data"

[ "(" "$current_major" -lt "$major_ver" ")" -o "(" \
"$current_major" -eq "$major_ver" -a \
"$current_minor" -lt "$minor_ver" ")" ] && perform_update="yes"

if [ -n "$perform_update" ] ; then
printf "$(date) -  [$prgname] - INFO ->  Performing an update ($current_version -> $major_ver.$minor_ver)\n"

BASE_PATH=""
[ $PACKAGE_TYPE = "ZIP" ] && BASE_PATH="products/commonupdater"

# Download the dat files...
# DownloadFile "$BASE_PATH$file_path" "$file_name" "bin" "$tmp_dir" \
# || exit_error "downloading '$file_name'"
download="$tmp_dir/$file_name"
# Did we get the dat update file?
[ -r "$download" ] || exit_error "unable to get $file_name file"

ValidateFile "$download" "$file_size" "$md5" \
|| exit_error "DAT update failed - File validation failed"
Update_$PACKAGE_TYPE "$install_dir" "$download" "$file_list" \
|| exit_error "updating DATs from file '$download'"

# Check the new version matches the downloaded one...
new_version=`GetCurrentDATVersion "$install_dir/$UVSCAN_EXE" "$UVSCAN_SWITCHES"`
[ -n "$new_version" ] \
|| exit_error "unable to get newly installed DAT version."
new_major=`echo "$new_version" | cut -d. -f-1`
new_minor=`echo "$new_version" | cut -d. -f2-`
printf "$(date) - [$prgname] - INFO -> current major version: ($major_ver)  new major version = ($new_major) current minor version: ($minor_ver) new minor version: ($new_minor)\n" 
if [ "$new_major" = "$major_ver" -a "$new_minor" = "$minor_ver" ]
then printf "$(date) - [$prgname] - INFO ->  DAT update succeeded $current_version -> $new_version\n"
else exit_error "DAT update failed - installed version different than expected\n"
fi
else
	printf "$(date) - [$prgname] - INFO ->  DAT already up to date ($current_version)\n"
fi

Cleanup ; exit 0
