#include "operations.h"

int add(int i, int j) {
    return i + j;
}

int minus(int i, int j) {
    return i - j;
} 

vector<int> histCalculate(vector<int>& frame, int H, int W){
    int i, j;
    vector<int> hist(256, 0);

    for (i=0;i<H;++i){
        for (j=0;j<W;++j){
            hist[frame[i*W+j]]++;
        }
    }

    return hist;
}

vector<int> frameReverse(vector<int>& frame, int H, int W){
    int i, j, k, rev_k;
    vector<int> reversed_frame(H*W*3, 0);

    for (i=0;i<H;++i){
        for (j=0;j<W;++j){
            k = 3*(i*W+j);  // pixel index
            rev_k = k + 3*(W-1-2*j);    // reversed pixel index
            reversed_frame[rev_k] = frame[k];   // B
            reversed_frame[rev_k + 1] = frame[k + 1];   // G
            reversed_frame[rev_k + 2] = frame[k + 2];   // R
        }
    }

    return reversed_frame;
}