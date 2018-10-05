'''
The old format for strings (until version 2)
was one string per file, resulting in lots of files
that are very annoying to edit.

This script agrupate the all in a json
'''

from os.path import isfile
from os import listdir


lang = 'es'
path = "text/"+lang


with open ('strings/'+lang+'.csv', 'w') as file:

    # write the headers
    file.write('action;text\n')

    for f in sorted(listdir(path)):
        print(f)
        # if it's a file
        if isfile(path+'/'+f):
            with open(path+'/'+f, 'r', encoding='utf-8') as txt_:
                #
                file.write(f.split('.')[0]+';"'+txt_.read()+'"\n')
