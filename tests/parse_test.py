
import csv

def main():
    '''
    '''
    with open('test_config.csv', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter="," , quotechar='|')
        next(reader)
        for test_config in reader:
            print(test_config)

            for ii in range(len(test_config)-1):
                print(test_config[0] +':' + test_config[ii+1])
            


if __name__ == '__main__':
    main()