#include <cmath>
#include <cstdlib>
#include <vector>
#include <complex>
#include <functional>
#include <algorithm>
#include "../intrin/alignedallocator.hpp"

template <class T>
inline T add(T a, T b){ return a+b; }

template <class T>
inline T mul(T a, T b){ return a*b; }


#define LOOP_COLLAPSE1 2
#define LOOP_COLLAPSE2 3
#define LOOP_COLLAPSE3 4
#define LOOP_COLLAPSE4 5
#define LOOP_COLLAPSE5 6

#include "kernel1.hpp"
#include "kernel2.hpp"
#include "kernel3.hpp"
#include "kernel4.hpp"
#include "kernel5.hpp"
