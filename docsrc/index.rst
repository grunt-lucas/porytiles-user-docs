Porytiles User Documentation
=============================

Welcome to the Porytiles user documentation! Porytiles is a command-line tool for compiling overworld tilesets for Pokemon Generation III decompilation projects.

.. note::

   This documentation is for Porytiles |release|. For documentation matching an older release,
   checkout the corresponding `git tag <https://github.com/grunt-lucas/porytiles-user-docs/tags>`_
   and build locally with ``cd docsrc && uv run make html``.

About This Documentation
------------------------

This guidebook is organized according to the `Diataxis framework <https://diataxis.fr/>`_, a systematic approach to technical documentation that distinguishes four types of content based on the reader's needs:

- **Explanation** (Background) --- understanding-oriented content that clarifies concepts, context, and the "why" behind the system. Read these pages when you want to build a mental model of how GBA tilesets and Porytiles work.
- **Tutorials** (Getting Started) --- learning-oriented, step-by-step walkthroughs that guide you through a complete task from start to finish. Follow these when you are new to Porytiles.
- **How-to Guides** --- task-oriented instructions for accomplishing specific goals. Consult these when you already understand the basics and need practical guidance for your daily workflow.
- **Reference** --- information-oriented, precise descriptions of configuration values, CLI commands, and data formats. Look things up here when you need exact details.

The **Topics** section is a pragmatic hybrid of explanation and reference for Porytiles subsystems (palette packing, tile sharing, animations, diagnostics) that are too complex for a pure reference listing but too detailed for a pure conceptual overview.

.. toctree::
   :maxdepth: 2
   :caption: Background

   gba-decomp-tileset-system
   manual-tileset-insertion
   porytiles-concepts

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   installation
   creating-your-first-tileset
   importing-an-existing-tileset

.. toctree::
   :maxdepth: 2
   :caption: How-to Guides

   compile-decompile-workflow

.. toctree::
   :maxdepth: 2
   :caption: Topics

   palette-packing
   tile-sharing
   animations
   diagnostics

.. toctree::
   :maxdepth: 2
   :caption: Reference

   metatile-attributes
   configuration
   cli-reference

Indices and tables
==================

* :ref:`genindex`
* :ref:`search`
