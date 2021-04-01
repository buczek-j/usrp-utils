#!/usr/bin/env python3

'''
Methods tp transorm from different nodes frames
global frame: 11x11
src/dest frames: 6x11
rly frames: 6x9
'''

def global_to_subframe(global_index, sub_frame_id):
    '''
    method to convert a global location index to a source/dest/rly location index
    :param global_index: int for the global location index
    :param sub_frame_id: string for the subframe ID ex: rly1, dest2 ... 
    :return int for the specified location frame index
    '''
    if 'src' in sub_frame_id or 'dest' in sub_frame_id:
        # 
        if '1' in sub_frame_id:
            return 6*(global_index//11) + global_index%11

        elif '2' in sub_frame_id:
            return 6*(global_index//11) + global_index%11 - 5

        else:
            print('UNKNOWN SUBFRAME NUMBER')
            return -1
    
    elif 'rly' in sub_frame_id:
        if '1' in sub_frame_id:
            return 6*(global_index//11 - 1) + global_index%11

        elif '2' in sub_frame_id:
            return 6*(global_index//11 - 1) + global_index%11 - 5

        else:
            print('UNKNOWN SUBFRAME NUMBER')
            return -1
    
    else:
        print('INVALID SUBFRAME ID')
        return -1


def subframe_to_global(subframe_index, sub_frame_id):
    '''
    method to convert a source/dest/rly location index to a global location index 
    :param subframe_index: int for the source/dest/rly location index
    :param sub_frame_id: string for the subframe ID ex: rly1, dest2 ... 
    :return int for the global location frame index
    '''
    if 'src' in sub_frame_id or 'dest' in sub_frame_id:
        # 
        if '1' in sub_frame_id:
            return 11*(subframe_index//6) + subframe_index%6

        elif '2' in sub_frame_id:
            return 11*(subframe_index//6) + subframe_index%6 + 5

        else:
            print('UNKNOWN SUBFRAME NUMBER')
            return -1
    
    elif 'rly' in sub_frame_id:
        if '1' in sub_frame_id:
            return 11*(subframe_index//6 + 1) + subframe_index%6

        elif '2' in sub_frame_id:
            return 11*(subframe_index//6 + 1) + subframe_index%6 + 5

        else:
            print('UNKNOWN SUBFRAME NUMBER')
            return -1
    
    else:
        print('INVALID SUBFRAME ID')
        return -1

def global_to_NED(global_index, scalar=2.0):
    '''
    Method to convert a global location index to meters north, meters east
    :param global_index: int for the global location index
    :param scalar: float for distance between points
    :return: list of floats for NED [meters north, meters east] 
    '''
    return [scalar*(global_index//11), scalar*(global_index%11)]

def main():
    '''
    '''
    while True:
        a = int(input('Input Global Index: '))
        uid = str(input('Input ID: '))
        b = global_to_subframe(a, uid)
        print("Global:", a, "Local "+uid+':',b)
        c = subframe_to_global(b, uid)
        print( "Local "+uid+':',b, "Global:", c)
        print()

if __name__ == '__main__':
    main()
