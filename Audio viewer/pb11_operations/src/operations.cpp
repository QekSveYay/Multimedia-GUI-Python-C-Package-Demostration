#include "operations.h"

using std::vector;

int volMeter(vector<int>& input, int input_size){
    int i;
    //int input_size = input.size();
    float tmp = 0.0;

    for (i=0;i<input_size;++i)
    {
        // Accumulate absolute value of each sample
        if ( input[i] < 0 )
        {
            tmp = tmp - (float)input[i];
        }
        else
        {
            tmp = tmp + (float)input[i];
        }
    }
    tmp = tmp / input_size;

    return (int)tmp;
}

vector<int> switchCH(vector<int>& input, int channel_size, int input_size){
    int i;
    vector<int> output(channel_size*input_size,0);;

    for (i=0;i<input_size;++i)
    {
        // switch each sample in left/right channel
        output[2*i+1] = input[2*i];
        output[2*i] = input[2*i+1];
    }

    return output;
}