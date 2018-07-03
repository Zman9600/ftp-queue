import os
import re
import ast
import sys
import shutil
import urllib
import ftputil

tobechecked = sys.argv[1] #Get list of ftp sites
totalsize = 0
maxitemsize = 209715200

if not os.path.exists('items'):
    os.makedirs('items')
if not os.path.exists('archive'): #Make these directories
    os.makedirs('archive')

def fixurl(itemurl):
    if re.search(r'^ftp:\/\/[^\/]+:21\/', itemurl): #Function to strip ":21" from end of sites
        itemurl = itemurl.replace(':21', '', 1)
    return itemurl

with open(tobechecked, 'r') as file: #Open the sites file
    ftps = file.read().splitlines() #Split it into lines
    for ftp in ftps:                            #For each file
        ftp = re.search(r'^(?:ftp:\/\/)?(.+)\/?$', ftp).group(1) #Get the bare ftp site and directory, ex. "ftp.example.com/test/"
        ftpdomain = re.search(r'^([^\/]+)', ftp).group(1)
        os.makedirs(ftpdomain) #Make a directory with the site's name
        os.chdir(ftpdomain) #Go into the directory
        itemftps = [] #Contains the domain name
        itemslist = [] #Contains the file or directory name
        itemsizes = [] #Contains the file size (0 for directories)
        startdir = '/'
        if re.search(r'^[^\/]+\/.+', ftp): #If site is like "ftp.example.com/directory/"
            startdir = re.search(r'^[^\/]+(\/.+)', ftp).group(1) #Make the starting directory "/directory/"
            if not startdir.endswith('/'): #Add a slash to the end of the directory if needed
                startdir += '/'
        with ftputil.FTPHost(ftpdomain,"Anonymous","Guest") as ftpconnection:
            for rootdir,dirlist,filelist in ftpconnection.walk(startdir,topdown=True,onerror=None):
                for dir in dirlist:
                    itemftps.append(ftpdomain)
                    itemslist.append('ftp://'+ftpdomain+ftpconnection.path.join(rootdir,dir)+"/")
                    itemsizes.append(0)
                    print('0, '+ftpconnection.path.join(ftpdomain,rootdir,dir)+"/")
                for files in filelist:
                    itemftps.append(ftpdomain)
                    itemslist.append('ftp://'+ftpdomain+ftpconnection.path.join(rootdir,files))
                    itemsizes.append(ftpconnection.path.getsize(ftpconnection.path.join(rootdir,files)))
                    print(str(ftpconnection.path.getsize(ftpconnection.path.join(rootdir,files)))+", "+ftpconnection.path.join(ftpdomain,rootdir,files))
        """
        while all(dir not in donedirs for dir in dirslist): #While there's directories we haven't done
            for dir in dirslist:
                dir = dir.replace('&#32;', '%20').replace('&amp;', '&') #Replace html character entity spaces and ampersands with %20 and &
                if re.search(r'&#[0-9]+;', dir): #If there are still html character entities, raise an exception
                    raise Exception(dir)
                dir = dir.replace('#', '%23') #URL encode the # symbol
                if not 'ftp://' + ftpdomain + dir in itemslist:
                    itemslist.append('ftp://' + ftpdomain + dir) #If the directory we're on isn't in the item list, add it
                    itemftps.append(ftpdomain)
                    itemsizes.append(0)
                if not 'ftp://' + ftpdomain + dir + './' in itemslist: #If the directory we're on isn't in the item list, add it
                    itemslist.append('ftp://' + ftpdomain + dir + './')
                    itemftps.append(ftpdomain)
                    itemsizes.append(0)
                if not 'ftp://' + ftpdomain + dir + '../' in itemslist: #If the directory we're on isn't in the item list, add it
                    itemslist.append('ftp://' + ftpdomain + dir + '../')
                    itemftps.append(ftpdomain)
                    itemsizes.append(0)
                for match in re.findall(r'([^\/]+)', dir):
                    if '/' + match + '/' + match + '/' + match + '/' + match + '/' + match in dir: #if the same directory name repeats over and over, we might be trapped in a directory loop, abort
                        break
                else:  #If we are not in a directory loop
                    if not dir in donedirs:  #If we haven't already done this directory
                        #Go to the FTP directory and store the result in ftp.example.com.html
                        os.system('wget --no-glob --timeout=20 --output-document=' + ftpdomain + '.html "ftp://' + ftpdomain + dir + '"')
                        if os.path.isfile(ftpdomain + '.html'): #If the file we tried to make exists
                            with open(ftpdomain + '.html', 'r') as index: #Open the file
                                for line in index.read().splitlines(): #Check each line
                                    if re.search(r'<a\s+href="ftp:\/\/[^\/]+[^"]+">', line): #If there's a link
                                        itemslist.append(re.search(r'<a\s+href="(ftp:\/\/[^\/]+[^"]+)">', line).group(1)) #Append the full URL to itemslist
                                        itemftps.append(ftpdomain) #Append the domain name to itemftps
                                    if re.search(r'<\/a>.*\(', line): #Find the end of the link and look for an item size
                                        itemsizes.append(int(re.search(r'<\/a>.*\(([0-9]+)', line).group(1))) #Append the item size to itemsizes
                                    elif re.search(r'<a\s+href="ftp:\/\/[^\/]+([^"]*)">', line) and ' Directory ' in line: #Look for a link to a path that says "Directory" on the same line
                                        dirslist.append(re.search(r'<a\s+href="ftp:\/\/[^\/]+([^"]+)">', line).group(1)) #Append the directory to dirslist as "/example/path/"
                                        itemsizes.append(0) #Append "0" to itemsizes
                                    elif re.search(r'<a\s+href="ftp:\/\/[^\/]+([^"]*)">', line):
                                        itemsizes.append(0)
                        donedirs.append(dir) #Append the directory we're on to donedirs
                        if os.path.isfile(ftpdomain + '.html'):
                            os.remove(ftpdomain + '.html') #Clean up the files we made
                        if os.path.isfile('wget-log'):
                            os.remove('wget-log') """
        os.chdir('..') #After all the directories are done, go up to the parent folder
        shutil.rmtree(ftpdomain) #Delete the directory we were working in
        totalitems = list(zip(itemftps, itemslist, itemsizes))
        archivelist = []
        newitems = []
        itemsize = 0
        itemnum = 0
        itemlinks = 0
        if os.path.isfile('archive/' + totalitems[0][0]): #If "/archive/ftp.example.com" exists
            with open('archive/' + totalitems[0][0]) as file: #Open it
                archivelist = [list(ast.literal_eval(line)) for line in file] #Put each line in the file into archivelist
        if os.path.isfile('archive/' + totalitems[0][0] + '-data'): #If "/archive/ftp.example.com-data" exists
            with open('archive/' + totalitems[0][0] + '-data', 'r') as file: #Open it
                itemnum = int(file.read()) + 1 #Put the number in the file into itemnum and add 1 to it.
        for item in totalitems: #For each file or directory we found
            if re.search(r'^(ftp:\/\/.+\/)[^\/]+\/', item[1]): #If it isn't the root directory or a file in the root directory
                if not (item[0], re.search(r'^(ftp:\/\/.+\/)[^\/]+\/', item[1]).group(1), 0) in totalitems: #If there's not an item for the item's parent directory
                    totalitems.append((item[0], re.search(r'^(.+\/)[^\/]+\/', item[1]).group(1), 0)) #Add the parent directory
                    totalitems.append((item[0], re.search(r'^(.+\/)[^\/]+\/', item[1]).group(1) + './', 0))
                    totalitems.append((item[0], re.search(r'^(.+\/)[^\/]+\/', item[1]).group(1) + '../', 0))
        for item in totalitems:
            itemurl = fixurl(item[1])
            if '&amp;' in itemurl or not [item[2], itemurl] in archivelist: #If the item has '&amp;' in it or the size and name isn't in the list (or has changed)
                newitems.append(item) #Add the item to newitems
        for item in newitems:
            print(item)
            itemdir = re.search(r'^(ftp:\/\/.+\/)', item[1]).group(1) #Get the directory the item is in, or the item if it is a directory
            while True:
                if not (item[0], itemdir, 0) in newitems: #If this directory isn't in newitems
                    newitems.append((item[0], itemdir, 0)) #Add it
                if re.search(r'^ftp:\/\/[^\/]+\/$', itemdir): #If we're in the root directory
                    break
                itemdir = re.search(r'^(ftp:\/\/.+\/)[^\/]+\/', itemdir).group(1) #Go up one directory
            itemurl = fixurl(item[1])
            with open('items/' + item[0] + '_' + str(itemnum), 'a') as file: #Make a new file and open it
                file.write(itemurl + '\n') #Write the url we need to update
                itemsize += item[2] #Add its size to the item size and total size
                totalsize += item[2]
                itemlinks += 1 #Count how many urls we need to visit
                if itemsize > maxitemsize or newitems[len(newitems)-1] == item: #If the item exceeds 210 MB or we run out of links
                    file.write('ITEM_NAME: ' + item[0] + '_' + str(itemnum) + '\n')
                    file.write('ITEM_TOTAL_SIZE: ' + str(itemsize) + '\n') #Write the item number, size, and number of links
                    file.write('ITEM_TOTAL_LINKS: ' + str(itemlinks) + '\n')
                    itemnum += 1
                    itemsize = 0
                    itemlinks = 0
            if not [item[2], itemurl] in archivelist:
                with open('archive/' + item[0], 'a') as file:
                    if "'" in itemurl:
                        file.write(str(item[2]) + ", \"" + itemurl + "\"\n")
                    else:
                        file.write(str(item[2]) + ', \'' + itemurl + '\'\n')
            with open('archive/' + totalitems[0][0] + '-data', 'w') as file:
                if os.path.isfile('items/' + item[0] + '_' + str(itemnum-1)):
                    file.write(str(itemnum-1))
        try:
            urllib.urlopen('ftp://' + ftpdomain + '/NONEXISTINGFILEdgdjahxnedadbacxjbc/')
        except Exception as error:
            dir_not_found = str(error).replace('[Errno ftp error] ', '')
            print(dir_not_found)

        try:
            urllib.urlopen('ftp://' + ftpdomain + '/NONEXISTINGFILEdgdjahxnedadbacxjbc')
        except Exception as error:
            file_not_found = str(error).replace('[Errno ftp error] ', '')
            print(file_not_found)

        if os.path.isfile('items/' + ftpdomain + '_dir_not_found'):
            os.remove('items/' + ftpdomain + '_dir_not_found')
        if os.path.isfile('items/' + ftpdomain + '_file_not_found'):
            os.remove('items/' + ftpdomain + '_file_not_found')

        with open('items/' + ftpdomain + '_dir_not_found', 'w') as file:
            file.write(dir_not_found)
        with open('items/' + ftpdomain + '_file_not_found', 'w') as file:
            file.write(file_not_found)

        if not tobechecked == 'to_be_rechecked':
            with open('to_be_rechecked', 'a') as file:
                if os.path.isfile('to_be_checked'):
                    file.write('\n' + ftp)
                else:
                    file.write(ftp)

print(totalsize)
