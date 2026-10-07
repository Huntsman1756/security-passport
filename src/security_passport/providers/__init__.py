"""Providers — acquisition boundaries.

Two contracts:

- ``InstrumentProvider`` — upstream instrument facts (today:
  OpenInstrument REST, plus fixtures). Never imported as a library.
- ``PassportStore`` — Security Passport's own generation stores
  (ECB assets, PRIII graphs, SSS/links topology, MIC registry,
  observations).
"""
