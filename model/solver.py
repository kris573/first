import sys, math
from input import Data
from gurobipy import *

if len(sys.argv) != 2:
    print("invalid options")
    print("example of use: ./solver.py input.txt")
    exit(1)

# Read input file
data = Data(sys.argv[1])
nodes = range(data.size)
model = Model("hub-location")
# model.setParam(GRB.Param.TimeLimit, 60 * 60 * 10.0) # 10 hour

# Aggregate demand (O_i and D_i)
O = [0] * data.size
D = [0] * data.size

for i in nodes:
    for j in nodes:
        O[i] += data.flow[(i, j)]

for i in nodes:
    for j in nodes:
        D[i] += data.flow[(j, i)]

# Variables
z = {}  # allocation
x = {}  # route

# z_kk
for i in nodes:
    for j in nodes:
        z[(i, j)] = model.addVar(vtype=GRB.BINARY, name="z_%d_%d" % (i, j))

# x_ijkm
for i in nodes:
    for j in nodes:
        for k in nodes:
            for m in nodes:
                x[(i, j, k, m)] = model.addVar(vtype=GRB.CONTINUOUS, name="x_%d_%d_%d_%d" % (i, j, k, m))

# Update model
model.update()

# Add constraints
# z_ik = 1
for i in nodes:
    model.addConstr(quicksum(z[(i, k)] for k in nodes) == 1)

# z_ik <= z_kk
for i in nodes:
    for k in nodes:
        if (i != k):
            model.addConstr(z[(i, k)] - z[(k, k)] <= 0)

# sum_m(x_ijkm) = Z_ik
for i in nodes:
    for j in range(i, data.size):
        for k in nodes:
            model.addConstr(quicksum(x[(i, j, k, m)] for m in nodes) - z[(i, k)] == 0)

# sum_k(x_ijkm) = Z_jm
for i in nodes:
    for j in range(i, data.size):
        for m in nodes:
            model.addConstr(quicksum(x[(i, j, k, m)] for k in nodes) - z[(j, m)] == 0)

# X_ijkm >= 0
for i in nodes:
    for j in nodes:
        for k in nodes:
            for m in nodes:
                model.addConstr(x[(i, j, k, m)] >= 0)

# Objective function
model.setObjective(
    quicksum(
        data.fixedCost[k]*z[(k, k)] for k in nodes
    ) + quicksum(
        (O[i] + D[i]) * data.cost[(i, k)] * z[(i, k)] for i in nodes for k in nodes if k != i
    ) + quicksum(
        (data.flow[(i, j)] * data.cost[(k, m)] * data.alpha + data.flow[(j, i)] * data.cost[(m, k)] * data.alpha) * x[(i, j, k, m)] for i in nodes for j in range(data.size) for k in nodes for m in range(data.size)
    )
)

# Save LP model and run
model.write('model.rlp')

model.modelSense = GRB.MINIMIZE
model.optimize()

# Print results
if model.status != GRB.OPTIMAL:
    print('No optimum solution found. Status: %i' % (model.status))

hubs = [k for k in nodes if z[(k, k)].X >= 0.9]
print("Result = %.4f" % model.objVal)
print("GAP = %.4f %%" % model.MIPGap)
print("Time = %.4f seg" % model.Runtime)
print("Hubs = ", hubs)
print("-------------")
print("FO, GAP, TIME, HUBS")
print("-------------")
print("%.4f,%.4f,%.4f,%d" % (model.objVal, model.MIPGap, model.Runtime, len(hubs)))
