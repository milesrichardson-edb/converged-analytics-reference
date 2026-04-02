# Spark 3.5.6 with Scala 2.13 + NVIDIA RAPIDS
# For use with PGAA Spark Connect GPU acceleration

FROM eclipse-temurin:17-jammy

ARG spark_uid=185

# RAPIDS JAR configuration
# RAPIDS_SOURCE: "maven" to download from Maven Central, "local" to use a provided JAR
ARG RAPIDS_SOURCE=maven
# RAPIDS_VERSION: version to download from Maven (e.g., "25.02.0")
ARG RAPIDS_VERSION=25.02.0
# RAPIDS_JAR: filename of local JAR (must be in build context) - used when RAPIDS_SOURCE=local
ARG RAPIDS_JAR=

RUN groupadd --system --gid=${spark_uid} spark && \
    useradd --system --uid=${spark_uid} --gid=spark spark

RUN set -ex; \
    apt-get update; \
    apt-get install -y gnupg2 wget bash tini libc6 libpam-modules krb5-user libnss3 procps net-tools gosu libnss-wrapper; \
    mkdir -p /opt/spark; \
    mkdir /opt/spark/python; \
    mkdir -p /opt/spark/examples; \
    mkdir -p /opt/spark/work-dir; \
    chmod g+w /opt/spark/work-dir; \
    touch /opt/spark/RELEASE; \
    chown -R spark:spark /opt/spark; \
    echo "auth required pam_wheel.so use_uid" >> /etc/pam.d/su; \
    rm -rf /var/lib/apt/lists/*

# Install Apache Spark 3.5.6 with Scala 2.13
ENV SPARK_TGZ_URL=https://archive.apache.org/dist/spark/spark-3.5.6/spark-3.5.6-bin-hadoop3-scala2.13.tgz \
    SPARK_TGZ_ASC_URL=https://archive.apache.org/dist/spark/spark-3.5.6/spark-3.5.6-bin-hadoop3-scala2.13.tgz.asc \
    GPG_KEY=0FE4571297AB84440673665669600C8338F65970

RUN set -ex; \
    export SPARK_TMP="$(mktemp -d)"; \
    cd $SPARK_TMP; \
    wget -nv -O spark.tgz "$SPARK_TGZ_URL"; \
    wget -nv -O spark.tgz.asc "$SPARK_TGZ_ASC_URL"; \
    export GNUPGHOME="$(mktemp -d)"; \
    gpg --batch --keyserver hkps://keys.openpgp.org --recv-key "$GPG_KEY" || \
    gpg --batch --keyserver hkps://keyserver.ubuntu.com --recv-keys "$GPG_KEY"; \
    gpg --batch --verify spark.tgz.asc spark.tgz; \
    gpgconf --kill all; \
    rm -rf "$GNUPGHOME" spark.tgz.asc; \
    \
    tar -xf spark.tgz --strip-components=1; \
    chown -R spark:spark .; \
    mv jars /opt/spark/; \
    mv RELEASE /opt/spark/; \
    mv bin /opt/spark/; \
    mv sbin /opt/spark/; \
    mv kubernetes/dockerfiles/spark/decom.sh /opt/; \
    mv examples /opt/spark/; \
    ln -s "$(basename /opt/spark/examples/jars/spark-examples_*.jar)" /opt/spark/examples/jars/spark-examples.jar; \
    mv kubernetes/tests /opt/spark/; \
    mv data /opt/spark/; \
    mv python/pyspark /opt/spark/python/pyspark/; \
    mv python/lib /opt/spark/python/lib/; \
    mv R /opt/spark/; \
    chmod a+x /opt/decom.sh; \
    cd ..; \
    rm -rf "$SPARK_TMP";

# Install RAPIDS plugin JAR - either download from Maven or copy local file
# For Maven: downloads rapids-4-spark_2.13-{version}.jar from Maven Central
# For local: copies the specified JAR file from build context
RUN if [ "$RAPIDS_SOURCE" = "maven" ]; then \
        echo "Downloading RAPIDS ${RAPIDS_VERSION} from Maven Central..."; \
        wget -nv -O /opt/spark/jars/rapids-4-spark_2.13-${RAPIDS_VERSION}.jar \
            "https://repo1.maven.org/maven2/com/nvidia/rapids-4-spark_2.13/${RAPIDS_VERSION}/rapids-4-spark_2.13-${RAPIDS_VERSION}.jar"; \
    fi

# Copy local JAR if using local source
# Uses .empty placeholder when no JAR specified (Maven mode)
COPY ${RAPIDS_JAR:-.empty} /tmp/rapids-local.jar
RUN if [ "$RAPIDS_SOURCE" = "local" ] && [ -n "$RAPIDS_JAR" ]; then \
        echo "Using local RAPIDS JAR: ${RAPIDS_JAR}"; \
        mv /tmp/rapids-local.jar /opt/spark/jars/${RAPIDS_JAR}; \
    else \
        rm -f /tmp/rapids-local.jar; \
    fi

# Copy GPU discovery script
COPY getGpusResources.sh /opt/spark/examples/src/main/scripts/
RUN chmod a+rx /opt/spark/examples/src/main/scripts/getGpusResources.sh

COPY entrypoint.sh /opt/
RUN chmod a+rx /opt/entrypoint.sh

ENV SPARK_HOME=/opt/spark

WORKDIR /opt/spark/work-dir

USER spark

ENTRYPOINT [ "/opt/entrypoint.sh" ]
