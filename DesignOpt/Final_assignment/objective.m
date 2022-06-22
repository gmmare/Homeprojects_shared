% xq = [0.1 0.6 0.0012 0.0012 0.0015 0.0015];
% objectivet(xq)
% 

function [f, b1, b2] = objective(x)
opt_params;

%analysis tools
W = GetWeight(x);
A = GetVolume(x);
if W<0
    disp('negative W:')
    disp(x)
end
if A<0
    disp('negative A:')
    disp(x)
end
%objective value
f_obj = (1-k)*(A/A_ref) + k*(W/W_ref);
% if f_obj<0
%     disp('negative:')
%     disp(x)
% end

%heave constraint
% h_max = constraint2(x)
% g1 = h_max/h_ref - 1;
% g2 = 0.6 * h_ref/h_max - 1;
p_max = constraints(x);
%flutter
g1 = p_max/p_ref - 1


%calculating barrier function
b1 = -(1/r) * log(-g1);
b2 = 0;%-(1/r) * log(-g2);

f = f_obj;

end

