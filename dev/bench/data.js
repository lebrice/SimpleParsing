window.BENCHMARK_DATA = {
  "lastUpdate": 1691094586978,
  "repoUrl": "https://github.com/lebrice/SimpleParsing",
  "entries": {
    "Python Benchmark with pytest-benchmark": [
      {
        "commit": {
          "author": {
            "email": "fabrice.normandin@gmail.com",
            "name": "Fabrice Normandin",
            "username": "lebrice"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "b3d12deca0207fef0e0c1db9c5ff404ca18da061",
          "message": "Increase import performance (lru_cache) and add pytest-benchmark (#279)\n\n* Add pytest-benchmark test dependency\r\n\r\nSigned-off-by: Fabrice Normandin <normandf@mila.quebec>\r\n\r\n* Add performance files for before the changes\r\n\r\nSigned-off-by: Fabrice Normandin <normandf@mila.quebec>\r\n\r\n* Use cached versions of inspect.getdoc/getsource\r\n\r\nFixes #278\r\n\r\nSigned-off-by: Fabrice Normandin <normandf@mila.quebec>\r\n\r\n* Make numpy import lazy\r\n\r\nSigned-off-by: Fabrice Normandin <normandf@mila.quebec>\r\n\r\n* Simplify the benchmark code a bit\r\n\r\nSigned-off-by: Fabrice Normandin <normandf@mila.quebec>\r\n\r\n* Remove .benchmarks file from git history\r\n\r\nSigned-off-by: Fabrice Normandin <normandf@mila.quebec>\r\n\r\n* Playing around with GitHub actions for benchmark\r\n\r\nSigned-off-by: Fabrice Normandin <normandf@mila.quebec>\r\n\r\n* Remove upload workflow, add benchmark\r\n\r\nSigned-off-by: Fabrice Normandin <normandf@mila.quebec>\r\n\r\n* Tweak benchmark.yml and build.yml\r\n\r\nSigned-off-by: Fabrice Normandin <normandf@mila.quebec>\r\n\r\n* Only run workflow on push to master\r\n\r\nSigned-off-by: Fabrice Normandin <normandf@mila.quebec>\r\n\r\n---------\r\n\r\nSigned-off-by: Fabrice Normandin <normandf@mila.quebec>",
          "timestamp": "2023-08-03T15:13:28-04:00",
          "tree_id": "4232ab8a244f811a298c5b2cf91118c6cd5f655b",
          "url": "https://github.com/lebrice/SimpleParsing/commit/b3d12deca0207fef0e0c1db9c5ff404ca18da061"
        },
        "date": 1691090042400,
        "tool": "pytest",
        "benches": [
          {
            "name": "test/test_performance.py::test_import_performance",
            "value": 83.49935177737817,
            "unit": "iter/sec",
            "range": "stddev: 0.00017047641604203258",
            "extra": "mean: 11.976140876711838 msec\nrounds: 73"
          },
          {
            "name": "test/test_performance.py::test_parse_performance",
            "value": 80.52313183346712,
            "unit": "iter/sec",
            "range": "stddev: 0.00014291956931091477",
            "extra": "mean: 12.418791684209912 msec\nrounds: 19"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "normandf@mila.quebec",
            "name": "Fabrice Normandin",
            "username": "lebrice"
          },
          "committer": {
            "email": "normandf@mila.quebec",
            "name": "Fabrice Normandin",
            "username": "lebrice"
          },
          "distinct": true,
          "id": "edb897e3ea52a7600787ce63d4bf88ad089017d1",
          "message": "Add an \"upload\" action for benchmark results\n\nSigned-off-by: Fabrice Normandin <normandf@mila.quebec>",
          "timestamp": "2023-08-03T16:29:01-04:00",
          "tree_id": "6314b6fd38c1bab3cbea41afaf9ccffda8cd011f",
          "url": "https://github.com/lebrice/SimpleParsing/commit/edb897e3ea52a7600787ce63d4bf88ad089017d1"
        },
        "date": 1691094586371,
        "tool": "pytest",
        "benches": [
          {
            "name": "test/test_performance.py::test_import_performance",
            "value": 83.18442762374737,
            "unit": "iter/sec",
            "range": "stddev: 0.0002325094334172115",
            "extra": "mean: 12.021480805555504 msec\nrounds: 72"
          },
          {
            "name": "test/test_performance.py::test_parse_performance",
            "value": 81.03641929369861,
            "unit": "iter/sec",
            "range": "stddev: 0.00017625019565362677",
            "extra": "mean: 12.340130631583323 msec\nrounds: 19"
          }
        ]
      }
    ]
  }
}