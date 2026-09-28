import numpy as np
def newsvendor_quantile(cu,co):
    if cu<0 or co<0 or cu+co<=0: raise ValueError("Cu/Co không hợp lệ")
    return cu/(cu+co)
def inventory_decision(lead_time_demand, inventory_position, cu, co):
    q=newsvendor_quantile(cu,co); target=float(np.quantile(lead_time_demand,q))
    rop=target; order=max(0.0,target-inventory_position)
    return {"critical_fractile":q,"reorder_point":rop,"order_up_to_target":target,"suggested_replenishment":order}
