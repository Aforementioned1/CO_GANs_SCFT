""" This program reads CSV data from a file (currently hardcoded as "scft_2.csv"),
and counts the amount of CSV entries with a "converged" value of "True" or an
"iterations" value of "2499", and prints each entry as well as the counts."""

import csv
import sys

iter = 0
conv = 0
i = 0
neither = 0

with open(sys.argv[1], "r") as f:
	reader = csv.DictReader(f)
	for r in reader:
		#print(r['iterations'])
		if r['converged'] == "True":
			print("CONV", r)
			i += 1
			conv += 1
		elif r['iterations'] == "2499":
			print("ITER", r)
			i += 1
			iter += 1

		else:
			# assumed to not have converged and not have maxed iterations
			neither += 1
			print("NEIT", r)



print("Number CONV(erged):", conv)
print("Number (fully) ITER(ated):", iter)
print("Number CONV(erged)/(fully) ITER(ated):", i)
print("Number NEIT(her)", neither)
