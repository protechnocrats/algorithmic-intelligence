# Sources for `skills/algorithmic-intelligence/references/techniques/data-at-scale.md`

Where each claim in that file comes from, for maintainers and reviewers. Not part of the installed skill.

- Alex Petrov, *Database Internals* (2019); Martin Kleppmann, *Designing Data-Intensive Applications* (2017).
- Patrick O'Neil et al., "The Log-Structured Merge-Tree (LSM-Tree)," *Acta Informatica* 33(4), 1996.
- Thomas M. Cover and Joy A. Thomas, *Elements of Information Theory*, 2nd ed. (2006): the source coding theorem; Huffman codes within one bit of the entropy.
- Manos Athanassoulis et al., "Designing Access Methods: The RUM Conjecture," EDBT 2016.
- Daniel Lemire, Gregory Ssi-Yan-Kai, and Owen Kaser, "Consistently Faster and Smaller Compressed Bitmaps with Roaring," *Software: Practice and Experience* 46(11), 2016; Sebastiano Vigna, "Quasi-Succinct Indices," WSDM 2013 (Elias-Fano for posting lists).
- Ralph C. Merkle, "A Digital Signature Based on a Conventional Encryption Function," CRYPTO 1987 (hash trees).
- Anil Shanbhag, Samuel Madden, and Xiangyao Yu, "A Study of the Fundamental Performance Characteristics of GPUs and CPUs for Database Analytics," SIGMOD 2020: with the GPU as a coprocessor, query time is bound by PCIe transfer and the CPU is faster; with the working set stored on the GPU, operators approach the GPU-to-CPU memory-bandwidth ratio.
- RAPIDS cuDF documentation, "Comparison of cuDF and pandas": joins and group-bys return rows in a nondeterministic order by default (use `sort=True`), and `sum` on floats is not guaranteed to match pandas or to repeat from run to run.
