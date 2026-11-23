ARM A' - SAME SOURCE ON CUDA 13.3, sm_86
========================================
Purpose: control arm for the sm_120 width cliff reported by Flaman. Question: does a current
toolkit change correctness or speed on Ampere?

Toolkit : CUDA 13.3 (13.3.73) installed root-free from the ubuntu2404 component debs into
          ~/opt/cuda-13.3 - cuda-nvcc, cuda-crt, cuda-cudart(+dev), cccl, libnvvm,
          libnvptxcompiler. nvcc reports "release 13.3, V13.3.73" and accepts sm_86 and sm_120.
Source  : 1.3.5 unchanged except the graph-node shim below.
Build   : python3 Source/build.py --archs 86
Window  : [1e24, 1e24 + 1e14), gap >= 1134

  shipped CUDA 12.8 sm86   215.6 s   0.463 T/s   432 gaps
  arm A'  CUDA 13.3 sm86   212.6 s   0.470 T/s   432 gaps

  identical (gap, lower) pairs 432   missing 0   extra 0   max |merit difference| 0.000000

So on sm86 a toolkit upgrade changes nothing that matters: same 432 gaps bit for bit, 1.4 % wall
difference (noise). The cliff is not a property of the source that a compiler upgrade would expose
on Ampere - it stays confined to sm_120.

THE ONLY SOURCE CHANGE

cudaGraphAddNode gained an edge-data argument in CUDA 13, and it sits *before* the dependency
count, not after:

  CUDA 12:  cudaGraphAddNode(node, graph, deps, numDeps, params)
  CUDA 13:  cudaGraphAddNode(node, graph, deps, edgeData, numDeps, params)

Rather than editing five call sites with a nullptr, this adds one version-portable shim so the
same source compiles on both toolchains:

  #if CUDART_VERSION >= 13000
  static inline cudaError_t scout_graph_add_node(cudaGraphNode_t *node, cudaGraph_t graph,
                                                 const cudaGraphNode_t *dependencies,
                                                 size_t count, cudaGraphNodeParams *params)
  { return cudaGraphAddNode(node, graph, dependencies, nullptr, count, params); }
  #else
  ... cudaGraphAddNode(node, graph, dependencies, count, params); ...
  #endif

Host-side only; it does not touch any kernel, and the 432/432 agreement confirms that.

NOT DONE HERE
  - No sm_120 build or run: this card is sm_86, and CUDA 13.3 can compile sm_120 but cannot run it.
  - The shipped binaries were restored after the test (sha256 c0bff48d... verified).
