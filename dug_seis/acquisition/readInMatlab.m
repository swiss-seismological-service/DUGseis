load('C:\Users\thaag\PycharmProjects\DUG-Seis\matlab\data-0.mat')

bytes_per_transfer = 32*1024*1024;
ram_buffer_size = 128*1024*1024;
fprintf('\nassuming the setup is: %d Mbyte bytes_per_transfer, %d Mbyte ram_buffer_size\n', bytes_per_transfer/1024/1024, ram_buffer_size/1024/1024)
fprintf('%d Mbyte bytes_per_transfer / 16 channels / 16 bit = %d "MByte" datapoints per channel per transfer\n',bytes_per_transfer/1024/1024, bytes_per_transfer/1024/1024/16/2)
fprintf('%d Mbyte ram_buffer_size / %d Mbyte bytes_per_transfer = %d transfers before ringbuffer starts at the beginning\n', ram_buffer_size/1024/1024, bytes_per_transfer/1024/1024, ram_buffer_size/bytes_per_transfer)

mb_of_samples = str2double(npts)/1024/1024;
fprintf('\nIn file:\n')
fprintf('%d "Mbyte" datapoints on this channel\n', mb_of_samples)
fprintf('%0.4f sec of data @ %d ksps\n', str2double(npts)/str2double(sampling_rate), str2double(sampling_rate)/1000)

plot(data,'x-', 'DisplayName', 'data')
hold on

point_nr = [1:mb_of_samples]*1024*1024;
plot(point_nr, data(point_nr),'o', 'DisplayName', 'last datapoint of bytes\_per\_transfer')
point_nr2 = 4*1024*1024;
plot(point_nr2, data(point_nr2),'d', 'DisplayName', 'last datapoint of ram\_buffer\_size')

legend show
hold off
%%
title('end of first transfer, beginning of second')
point_nr = 1*1024*1024;
x_width = 50;
y_width = 50;

xlim([point_nr-x_width point_nr+x_width])
ylim([data(point_nr)-y_width data(point_nr)+y_width])

%%
title('end of ram buffer, with simulated data there can be a jump here')
point_nr = 4*1024*1024;
x_width = 50;
y_width = 50;

xlim([point_nr-x_width point_nr+x_width])
ylim auto
%%
xlim auto
ylim auto
