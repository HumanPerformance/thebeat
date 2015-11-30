%
% Identify S1
%
% This function uses the principles of autocorrelation to identify the S1
% signals within auscultation recordings
%
% Fluvio L Lobo Fenoglietto


function [excision] = signalid(audiodata,extract,conv)

    signal = audiodata.signal;
    time = audiodata.time;
    extract = extract.signal;
    % conv = 0.96;

    % vector lengths
    Nsignal = length(signal);
    Nextract = length(extract);

    % signal autocorrelation
    % the autocorrelation of the extract is used to calculate a
    % normalization coefficient
    aCorr = 0;
    for i = 1:Nextract
        aCorr = aCorr + extract(i)*extract(i);
    end % end of for-loop

    % signal cross-correlation
    % the "cross-correlation" routine below does not follow the exact
    % mathematical formulation of cross-correlation. In general, the
    % extract (the shorter signal) is sweeped through the signal, starting
    % and finishing with a complete overlay of the extract.
    cCorr = zeros(Nsignal-Nextract,1);
    for i = 1:Nsignal-Nextract  
        for j = 1:Nextract       
            cCorr(i) = cCorr(i) + signal(i+j-1)*extract(j);       
        end
        % cross correlation normalization
        % the auto-correlation coefficient is used to normalize the
        % comparison to 1, allowing the user to specify an arbitrary
        % convergence tolerance parameter.
        nCorr(i) = cCorr(i)/aCorr;
        if nCorr(i) > conv
            break
        end % end of if-statement
    end % end of for-loop

    % excising region of correlation
    corrindex = find(nCorr > conv);
    excision = signal(corrindex:corrindex+Nextract-1);
    
    % create dummy array for visualization
    nCplot = zeros(Nsignal,1);
    for i = corrindex:corrindex+Nextract-1
        nCplot(i) = excision(i-corrindex+1,1);
    end
    
    % plotting signal match
    figure,
    plot(time,signal,'b')
    hold on
    plot(time,nCplot,'r')
    xlabel('Time (sec.)');
    ylabel('Amplitude (V)');
    legend('Signal','Extract');
    grid on
   
end % End of function