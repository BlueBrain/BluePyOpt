try:
    import arbor
except ImportError as e:
    class arbor:
        def __getattribute__(self, _):
            raise ImportError("Exporting cell models to ACC/JSON, loading"
                              " them or optimizing them with the Arbor"
                              " simulator requires missing dependency arbor."
                              " To install BluePyOpt with arbor,"
                              " run 'pip install bluepyopt[arbor]'.")
