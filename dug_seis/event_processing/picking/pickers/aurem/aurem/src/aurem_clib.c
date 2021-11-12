// gcc -shared -Wl,-soname,aurem_c -O3 -o aurem_c.so -fPIC aurem_c.c

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

// Declare Functions

int aicp(float* arr, int sz, /*@out@*/ float* aic, int* minidx);
int recp(float *arr, int sz, /*@out@*/ float* aic, int* minidx);



/* ------------  MyHELP

int A[5]
Address: &A[i] OR (A+i)
Value:    A[i]  OR *(A+i)

%p requires an argument of type void*, not just of any pointer type.
If you want to print a pointer value, you should cast it to void*:
printf("&q = %p\n", (void*)&q);

https://www.youtube.com/watch?v=CpjVucvAc3g

int (*pp)[ii - 0 + 1] = (int (*)[ii - 0 + 1])&arr[0];  //orig

# AIC(k)=k*log(variance(x[1,k]))+(n-k-1)*log(variance(x[k+1,n]))
-------------- */


int aicp(float* arr, int sz, /*@out@*/ float* aic, int* pminidx) {

    // Declare MAIN
    int ii;  // MAIN loop
    int minidx = 0;
    float minval = INFINITY;
    float var1, var2, val1, val2;
    memset(aic, 0, (sz-1)*sizeof(float));  // or sz-1 ???

    // Declare VARIANCE
    float sd;
    int _x, _xx, _y, _yy; // AUX loop
    float sumOne, meanOne;
    float sumTwo, meanTwo;
    float devOne, sdevOne;
    float devTwo, sdevTwo;
    //
    float valOne, valTwo;


    // Work
    for (ii=1; ii<sz; ii++) {

        // Loop for VAR 1
        sumOne = 0.0;
        for (_x=0; _x<ii; _x++){
            sumOne = sumOne + arr[_x];
        }
        meanOne = sumOne / ii;

        sdevOne = 0.0;
        for (_xx=0; _xx<ii; _xx++){
            devOne = (arr[_xx] - meanOne) * (arr[_xx] - meanOne);
            sdevOne = sdevOne + devOne;
        }
        //var1 = sdevOne / ii;
        //sd = sqrt(var1);
        valOne = ii * log(sdevOne / ii);



        // Loop for VAR 2
        sumTwo = 0.0;
        for (_y=ii; _y<sz; _y++){
            sumTwo = sumTwo + arr[_y];
        }
        meanTwo = sumTwo / (sz - ii);

        sdevTwo = 0.0;
        for (_yy=ii; _yy<sz; _yy++){
            devTwo = (arr[_yy] - meanTwo) * (arr[_yy] - meanTwo);
            sdevTwo = sdevTwo + devTwo;
        }
        //var2 = sdevTwo / (sz - ii);
        //sd = sqrt(var2);
        valTwo = (sz - ii - 1) * log(sdevTwo / (sz - ii));

        // Allocate to AIC
        aic[ii - 1] = (valOne + valTwo);

        // Find MINIMA

        if ( isinf(aic[ii-1]) ) {
            aic[ii-1] = INFINITY;
        }

        if ( isnan(aic[ii-1]) ) {
            aic[ii-1] = INFINITY;
        }


        // Not minor equal, but just equal
        if (aic[ii-1] < minval) {
            minval = aic[ii-1];
            minidx = ii-1;
        }
    }
    //
    *pminidx = minidx;  // return IDX
    return 0;
}



int recp(float *arr, int sz, /*@out@*/ float* aic, int* minidx)
{
    printf("Hello World\n");
}



/* AIC[ii]
var1 = np.log(np.var(arr[0:ii]))
var2 = np.log(np.var(arr[ii:]))
val1 = ii * var1
val2 = (arr.size - ii - 1) * var2
self.aicfn[ii - 1] = (val1 + val2)
*/

/*  =================================== HELPER VARIANCE
float calcvar(int *x, int szx)
{
    int i;
    float sum;
    float mean;
    float dev, sdev;
    float var;


    for(i = 1; i <= szx; ++i){
        sum = sum + x[i];
    }
    mean = sum / szx;

    for(i = 1; i <= szx; ++i){
        dev = (x[i] - mean)*(x[i] - mean);
        sdev = sdev + dev;
    }
    var = sdev / (szx - 1);
    // sd = sqrt(var);
    return var;

 =================================== */
