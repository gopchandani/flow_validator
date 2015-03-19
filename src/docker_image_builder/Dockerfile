#VERSION               1.0
FROM      ubuntu
MAINTAINER Shane Rogers <shane@shanerogers.info>

# Specify container username e.g. training, demo
ENV VIRTUSER admin
ENV JAVA_HOME /usr/lib/jvm/java-7-openjdk-amd64/jre
ENV PATH $JAVA_HOME/bin:$PATH
EXPOSE 6633

RUN apt-get update -qq
RUN sudo apt-get install -y wget
RUN sudo apt-get install -y --no-install-recommends openjdk-7-jdk
RUN sudo  wget https://nexus.opendaylight.org/content/groups/public/org/opendaylight/integration/distribution-karaf/0.2.1-Helium-SR1/distribution-karaf-0.2.1-Helium-SR1.tar.gz && tar -xzvf distribution-karaf-0.2.1-Helium-SR1.tar.gz
RUN sudo rm distribution-karaf-0.2.1-Helium-SR1.tar.gz

RUN wget https://www.dropbox.com/s/yfelsjzji2k0owo/karaf_config.tar.gz 
#RUN tar -xzvf karaf_config.tar.gz -C /distribution-karaf-0.2.1-Helium-SR1/etc/opendaylight/karaf/
RUN cp karaf_config.tar.gz /distribution-karaf-0.2.1-Helium-SR1/etc/opendaylight/karaf/
RUN cd /distribution-karaf-0.2.1-Helium-SR1/etc/opendaylight/karaf/
RUN tar -xzvf karaf_config.tar.gz
