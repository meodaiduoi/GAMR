import os
import logging

'''
    Env management

'''
def set_cwd_to_location(filepath):
    '''
        Used to set current working dir 
        of file to desier path     
    '''
    filepath = os.path.abspath(filepath)
    os.chdir(os.path.dirname(filepath))

def mkdir(path):
    '''
        For making 
    '''
    if not os.path.exists(path):
        os.makedirs(path)
        logging.info(f"Folder: {path} created")
