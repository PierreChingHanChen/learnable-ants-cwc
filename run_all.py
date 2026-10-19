"""Run every CwC experiment, the revision analysis and the figure scripts in order.

    python run_all.py              # full data (several hours on two CPU cores)
    QUICK=1 python run_all.py      # smoke test with tiny samples (minutes; overwrites results/)
    python run_all.py exp12 exp10b # only the named steps (exp1 runs exp1 only, not exp10–exp13)

Each step is (name, script, extra environment variables). Seed counts and other
settings default to the values used in the paper (see docs/en/EXPERIMENTS.md).
Per-experiment text summaries are written to results/summary_*.md (generated
logs, in Chinese; not tracked by git). Curated bilingual results are in docs/.
"""
import os
import runpy
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "experiments"))
sys.path.insert(0, HERE)

STEPS = [
    # platform validation (text S2) and traveling-salesman / sorting experiments
    ("exp1_tsp_params", "exp1_tsp_params", {}),
    ("exp2_tsp_compare", "exp2_tsp_compare", {}),
    ("exp3_sorting", "exp3_sorting", {}),
    ("exp4_topic1_we_sense", "exp4_topic1_we_sense", {}),
    ("exp5_topic2_responsibility", "exp5_topic2_responsibility", {}),
    ("exp6_topic3_reversibility", "exp6_topic3_reversibility", {}),
    ("exp7_topic2_stats", "exp7_topic2_stats", {}),
    ("exp8_topic3_controls", "exp8_topic3_controls", {}),
    # learnable (microGPT) ants
    ("exp9_microgpt_ants", "exp9_microgpt_ants", {}),
    ("exp10_topic2_learnable", "exp10_topic2_learnable", {}),
    ("exp10b_confirmatory", "exp10_topic2_learnable",
     {"EXP10_SEED0": "1000", "EXP10_SHAPLEY": "12", "EXP10_TAG": "b"}),
    ("exp11_d1_controls", "exp11_d1_controls", {}),
    ("exp12_learnable_return", "exp12_learnable_return", {}),
    ("exp13_grammar_adherence", "exp13_grammar_adherence", {}),
    # analysis and figures
    ("fig_data", "fig_data", {}),
    ("analysis_revision", "analysis_revision", {}),
    ("make_figures", "make_figures", {}),
    ("make_supp_figures", "make_supp_figures", {}),
]

if __name__ == "__main__":
    only = sys.argv[1:]
    for name, script, env in STEPS:
        if only and not any(name == o or name.startswith(o + "_") for o in only):
            continue
        saved = {k: os.environ.get(k) for k in env}
        os.environ.update(env)
        t = time.time()
        print(f"\n===== {name} =====")
        argv, sys.argv = sys.argv, [script + ".py"]
        try:
            runpy.run_path(os.path.join(HERE, "experiments", script + ".py"), run_name="__main__")
        finally:
            sys.argv = argv
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        print(f"[{name}] {time.time() - t:.0f}s")
