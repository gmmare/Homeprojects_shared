function [f_sum] = objective_mask(alpha, xq, sq)
%getting optimizer parameters
opt_params;

% line searching
x_des = xq + alpha*sq; 

%objective value
[f, b1, b2, g1, g2] = objective(x_des);
f_sum = f + b1 + b2;
end

