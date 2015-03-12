import numpy as np
import matplotlib.pyplot as plt

# example data
x = np.arange(0.1, 4, 0.5)
y1 = np.exp(-x)
y2 = np.exp(-2*x)


print type(x)
print type(y1)

plt.errorbar(x, y1, yerr=0.05)
plt.errorbar(x, y2, yerr=0.05)

plt.xlabel("Number of switches in the ring")
plt.ylabel("Computation Time(ms)")
plt.show()


# Assuming that x-axis are keys to the data_dict
#def plot_varying_size_topology(data_dict):

