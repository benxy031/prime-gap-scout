SM86 COUNTER-EVIDENCE FOR THE RTX 5070 BIT-WIDTH CLIFF
======================================================
Local run: RTX 3070 (sm86, 46 SMs), CUDA 12.4.131, Linux
Binary: Source/frontend/bin/pgn68-worker-sm86-k32  (Scout 1.3.5, committed build)
Command: ./pgn68-worker-sm86-k32 --engine walk --start <S> --length 1e13 --device 0 --gap-min <G>
Length 1e13 (Flaman used 1e14); worker seconds include initialisation.

  start   bits  engine (logged)      gap-min   seconds   T/s
  ---------------------------------------------------------------
  1e20     67   (narrow_euler)         946      16.60    0.603
  1e21     70   (radix3)               992      17.75    0.563
  1e22     74   euler74               1040      19.00    0.526
  3e22     75   (euler75)             1062      20.70    0.483
  1e23     77   (pairs76_77)          1086      20.81    0.481
  1e24     80   (float80)             1134      21.59    0.463
  1e25     84   (pairs81_87)          1182      23.50    0.426
  1e26     87   (pairs81_87)          1228      25.06    0.399
  1e27     90   (pairs88_94)          1276      25.85    0.387
  1e28     94   (pairs88_94)          1322      28.74    0.348

Engine selection confirmed by the worker's own log line, e.g. at 1e22:

  [pgn-selected-backend] family=euler74 high=542 gap_min=1040 profile_k=32
                         coverage=67_95_all_high_words

THE POINT

The curve is smooth and monotone on sm86: 0.603 down to 0.348 T/s. There is no 6x step at any
width, and 74 bits - the slowest row in Flaman's table at 0.157 T/s - runs at 0.526 T/s here,
i.e. 3.35x faster on a card that is otherwise ~1.7x slower than his 5070.

Same engine, same source, same dispatch, opposite behaviour. So the cliff is not the kernel
selection and not the algorithm; it is specific to the sm_120 build.

WHAT THE SLOW SET HAS IN COMMON

Every width that is slow on the 5070 maps to a kernel that contains inline PTX carry chains
(`add.cc.u32` / `addc.cc.u32`):

  slow  radix3_upper (73-74), pairs76_77, pairs78_79, pairs81_87, pairs88_94, retained95
  fast  narrow_euler (66-68), euler69, radix3 (70-71), euler72, euler75, float80

  grep -ln 'add\.cc\.u32' Source/native/*.cuh
  -> barrett70-exact, euler96, extended_columns, optimized_pairs76_77, optimized_pairs78_79,
     optimized_pairs81_87, optimized_pairs88_94, optimized_radix3_upper, optimized_retained95,
     optimized_retained95_low, retained_columns, wide_math

  fast kernels: none of them contains it. barrett70-exact has it but is only the cold fallback
  behind pgn_barrett70::test(low), which is why 70 bits stays fast.

Each of those files already carries a plain-C++ branch for the same three-limb add, guarded by
`#if defined(__CUDA_ARCH__)` ... `#else`, so the portable form exists in tree and is used off
device today.

HYPOTHESIS

On sm_120 (Blackwell) the inline carry-chain asm does not compile to an efficient sequence - or
defeats whatever the compiler would otherwise schedule - and costs 5-6x. On sm_86 the same asm
compiles fine, which is why the cliff does not reproduce here.

HOW TO CONFIRM, ON A 50-SERIES CARD

  1. Rebuild with the plain-C++ branch selected for sm_120 only (`__CUDA_ARCH__ >= 1200`), leaving
     sm_86 untouched, and re-run 74/77/84/90. If those three rows jump to ~0.5 T/s, the cause is
     confirmed.
  2. Or disassemble the sm_120 cubin for the eight slow kernels and compare the carry-sequence
     SASS against the sm_86 build of the same source.

WHAT NOT TO DO

Do not change the arithmetic. The C++ fallback is the same three-limb add; swapping it changes
scheduling, not results. But it must be validated on sm_120 with a bit-identical gap list, not
just a timing check - these kernels produce the primality witness, and the network pins the
native source manifest hash, so any source change also requires a new qualified release before a
node can use it.
