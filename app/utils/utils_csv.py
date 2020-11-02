def merge_files_into_one(files_to_merge, output_file):
    with open(output_file, 'w') as outfile:
        for fname in files_to_merge:
            with open(fname) as infile:
                for line in infile:
                    outfile.write(line)